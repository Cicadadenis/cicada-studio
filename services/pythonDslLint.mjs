import fs from 'fs';
import os from 'os';
import path from 'path';
import { spawnSync } from 'child_process';

const MAX_CODE_BYTES = Number(process.env.DSL_MAX_CODE_BYTES || 100_000);

function pythonCmd() {
  const fromEnv = process.env.PYTHON || process.env.PYTHON3;
  if (fromEnv) return fromEnv;
  if (process.platform === 'win32') return 'python';
  // В non-interactive контейнерах pyenv-shim для python3 может зависать на
  // разрешении версии. Системный Python даёт тот же парсеру интерпретатор без
  // лишнего shim-слоя и корректно завершается по timeout.
  if (fs.existsSync('/usr/bin/python3')) return '/usr/bin/python3';
  return 'python3';
}


function findUnsupportedBlockComment(line) {
  let inQuote = false;
  let escaped = false;
  const text = String(line || '');
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch === '\\') {
      escaped = inQuote;
      continue;
    }
    if (ch === '"') {
      inQuote = !inQuote;
      continue;
    }
    if (!inQuote && text.slice(i).match(/^#\s*блок\s+/)) return i;
  }
  return -1;
}

function unsupportedBlockCommentDiagnostics(code) {
  return String(code || '')
    .replace(/\r\n/g, '\n')
    .split('\n')
    .map((line, idx) => ({ line, idx, col: findUnsupportedBlockComment(line) }))
    .filter((row) => row.col !== -1)
    .map((row) => ({
      type: 'UnsupportedBlockComment',
      code: 'DSL-UNSUPPORTED-BLOCK-COMMENT',
      severity: 'error',
      line: row.idx + 1,
      column: row.col + 1,
      offset: row.col + 1,
      message: 'Неподдерживаемый блок сгенерирован как комментарий «# блок ...» и не будет выполняться ботом.',
      sourceLine: row.line,
      help: 'Замените комментарий на реальную инструкцию DSL, например «запустить имя_сценария», или пересоберите блоки в конструкторе.',
      suggestions: [],
    }));
}

/**
 * Запускает Python-парсер Cicada для проверки DSL-кода.
 *
 * @param {{ code: string, cwd?: string }} opts
 * @returns {{
 *   ok: boolean,
 *   available: boolean,
 *   diagnostics: Array<{code:string, severity:string, line:number, message:string, help:string}>,
 *   error?: string
 * }}
 */
export function lintCicadaWithPython(opts) {
  const code = String(opts.code ?? '');
  const timeoutMs = Math.max(
    1_000,
    Math.min(15_000, Number.isFinite(Number(opts.timeoutMs)) ? Number(opts.timeoutMs) : 15_000),
  );

  const unsupportedCommentDiags = unsupportedBlockCommentDiagnostics(code);
  if (unsupportedCommentDiags.length) {
    return {
      ok: false,
      available: true,
      diagnostics: unsupportedCommentDiags,
      error: 'DSL содержит неподдерживаемые комментарии «# блок ...» вместо исполняемых инструкций.',
    };
  }

  // ── слишком большой код ──────────────────────────────────────────────────
  if (Buffer.byteLength(code, 'utf8') > MAX_CODE_BYTES) {
    return {
      ok: false,
      available: true,
      diagnostics: [],
      error: `Код слишком большой для проверки (>${MAX_CODE_BYTES} байт)`,
    };
  }

  // ── пишем во временный файл ──────────────────────────────────────────────
  const tmp = path.join(os.tmpdir(), `cicada-lint-${process.pid}-${Date.now()}.ccd`);
  try {
    const CICADA_HEADER = '# Cicada3301';
    const finalCode = code.trimStart().startsWith(CICADA_HEADER) ? code : CICADA_HEADER + '\n' + code;
    fs.writeFileSync(tmp, finalCode, 'utf8');

    const py = pythonCmd();
      const bootstrap = `
import io, json, sys
from pathlib import Path
from cicada.parser import Parser

path = Path(sys.argv[1]).resolve()
source = path.read_text(encoding='utf-8')
try:
    Parser(source, base_path=str(path.parent)).parse()
    print(json.dumps({"ok": True, "available": True, "diagnostics": []}, ensure_ascii=False))
    sys.exit(0)
except SyntaxError as e:
    lineno = int(getattr(e, 'lineno', None) or 1)
    msg = getattr(e, 'msg', None) or (e.args[0] if e.args else str(e)) or str(e)
    offset = getattr(e, 'offset', None)
    text = getattr(e, 'text', None)
    column = offset if isinstance(offset, int) else None
    src_line = text.rstrip('\\n') if isinstance(text, str) else None
    diag = {
        "type": "SyntaxError",
        "code": "DSL-PY",
        "severity": "error",
        "line": lineno,
        "column": column,
        "offset": offset if isinstance(offset, int) else None,
        "message": str(msg),
        "sourceLine": src_line,
        "help": "Проверь синтаксис строки.",
        "suggestions": [],
    }
    print(json.dumps({"ok": False, "available": True, "diagnostics": [diag]}, ensure_ascii=False))
    sys.exit(1)
except Exception as e:
    diag = {
        "type": "ParserError",
        "code": "DSL-PY",
        "severity": "error",
        "line": 1,
        "column": None,
        "offset": None,
        "message": str(e),
        "sourceLine": None,
        "help": str(e),
        "suggestions": [],
    }
    print(json.dumps({"ok": False, "available": True, "diagnostics": [diag]}, ensure_ascii=False))
    sys.exit(1)
`.trim();

      const proc = spawnSync(py, ['-c', bootstrap, tmp], {
        cwd: os.tmpdir(),
        encoding: 'utf8',
        maxBuffer: 2 * 1024 * 1024,
        windowsHide: true,
        shell: false,
        timeout: timeoutMs,
        env: {
          PATH: process.env.PATH,
          HOME: process.env.HOME,
          PYTHONUTF8: '1',
          PYTHONIOENCODING: 'utf-8',
          PYTHONUNBUFFERED: '1',
        },
      });

    const errText = (proc.stderr || '').trim();

    // ── Python не найден или упал с OS-ошибкой ────────────────────────────
    if (proc.error) {
      const msg =
        proc.error.code === 'ENOENT'
          ? `Python не найден (${py}). Укажите переменную PYTHON в .env.`
          : proc.error.message;
      return { ok: false, available: false, diagnostics: [], error: msg };
    }

    const out = String(proc.stdout || '').trim();

    // ── парсим JSON-ответ ────────────────────────────────────────────────
    let data = null;
    try {
      data = JSON.parse(out);
    } catch {
      return {
        ok: false,
        available: false,
        diagnostics: [],
        error: errText || out || `python lint завершился с кодом ${proc.status}`,
      };
    }

    // Нормализуем поля
    if (data.available == null) data.available = true;
    if (!Array.isArray(data.diagnostics)) data.diagnostics = [];

    return data;

  } finally {
    try { fs.unlinkSync(tmp); } catch { /* noop */ }
  }
}

/**
 * Обёртка для AI-пайплайна: бросает ошибку если парсер недоступен или нашёл проблемы.
 * Используется в /api/ai-generate чтобы ГАРАНТИРОВАТЬ прохождение через парсер.
 *
 * @param {string} dslCode — сгенерированный DSL
 * @param {{ cwd?: string }} opts
 * @throws {Error} если парсер недоступен ИЛИ нашёл синтаксические ошибки
 */
export function requireParsedDSL(dslCode, opts = {}) {
  const result = lintCicadaWithPython({ code: dslCode, ...opts });

  // Парсер недоступен — блокирующая ошибка
  if (!result.available) {
    const e = new Error(
      `Парсер Cicada недоступен — невозможно проверить DSL от AI. ` +
        `${result.error || 'Проверьте наличие Python и установленного пакета Cicada'}`
    );
    e.parserUnavailable = true;
    throw e;
  }

  // Парсер нашёл ошибки
  if (!result.ok || result.diagnostics.length > 0) {
    const msgs = result.diagnostics
      .slice(0, 5)
      .map((d) => {
        const line = d.line != null ? ` (стр. ${d.line})` : '';
        return `${d.message || d.code || 'ошибка'}${line}`;
      })
      .join('; ');
    const e = new Error(msgs || result.error || 'Парсер Cicada отклонил DSL');
    e.parserRejected = true;
    e.diagnostics = result.diagnostics;
    throw e;
  }

  return result;
}

/**
 * Получает DSL-aware hints из установленного пакета Cicada.
 * Возвращает пустой список, если модуль/интерпретатор недоступен.
 */
export function getDslHintsWithPython(opts) {
  const code = String(opts.code ?? '');
  const py = pythonCmd();
  const bootstrap = `
import json, sys
from pathlib import Path
try:
    from cicada.hints import dsl_aware_hints
except Exception as e:
    print(json.dumps({"ok": False, "hints": [], "error": str(e)}, ensure_ascii=False))
    sys.exit(0)

src = Path(sys.argv[1]).read_text(encoding='utf-8')
print(json.dumps({"ok": True, "hints": dsl_aware_hints(src)}, ensure_ascii=False))
`.trim();

  const tmp = path.join(os.tmpdir(), `cicada-hints-${process.pid}-${Date.now()}.ccd`);
  try {
    const CICADA_HEADER = '# Cicada3301';
    const finalCode = code.trimStart().startsWith(CICADA_HEADER) ? code : CICADA_HEADER + '\n' + code;
    fs.writeFileSync(tmp, finalCode, 'utf8');
    const proc = spawnSync(py, ['-c', bootstrap, tmp], {
      cwd: os.tmpdir(),
      encoding: 'utf8',
      maxBuffer: 2 * 1024 * 1024,
      windowsHide: true,
      shell: false,
      timeout: 15_000,
      env: {
        PATH: process.env.PATH,
        HOME: process.env.HOME,
        PYTHONUTF8: '1',
        PYTHONIOENCODING: 'utf-8',
        PYTHONUNBUFFERED: '1',
      },
    });
    if (proc.error) return { ok: false, hints: [], error: proc.error.message };
    const out = String(proc.stdout || '').trim();
    if (!out) return { ok: false, hints: [], error: String(proc.stderr || '').trim() || 'empty hints output' };
    try {
      const parsed = JSON.parse(out);
      return parsed && typeof parsed === 'object' ? parsed : { ok: false, hints: [] };
    } catch {
      return { ok: false, hints: [], error: out };
    }
  } finally {
    try { fs.unlinkSync(tmp); } catch { /* noop */ }
  }
}
