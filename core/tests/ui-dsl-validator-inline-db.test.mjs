import test from 'node:test';
import assert from 'node:assert/strict';
import { validateDSL, isInlineDbInstructionLine } from '../validator/uiDslValidator.js';

test('isInlineDbInstructionLine detects inline from db rows', () => {
  assert.equal(isInlineDbInstructionLine('inline из бд "категории" callback "category:"'), true);
  assert.equal(isInlineDbInstructionLine('    inline из бд "x"'), true);
  assert.equal(isInlineDbInstructionLine('ответ "hi"'), false);
});

test('validateDSL does not treat inline-db DSL keywords as undefined variables', () => {
  const code = `бот "YOUR_BOT_TOKEN"

при старте:
    ответ "Меню"
    inline из бд "категории" callback "category:" назад "⬅️ Назад" → "назад" колонки 2

при нажатии:
    если начинается_с(кнопка, "category:"):
        запомни категория = срез(кнопка, 9)
        ответ "{категория}"`;
  const { warnings } = validateDSL(code, []);
  const varWarnings = warnings.filter((w) => w.includes('нигде не определена'));
  const falsePositives = ['бд', 'callback', 'назад', 'колонки'];
  for (const name of falsePositives) {
    assert.equal(
      varWarnings.some((w) => w.includes(`"${name}"`)),
      false,
      `expected no warning for DSL keyword ${name}, got: ${varWarnings.join('; ')}`,
    );
  }
});
