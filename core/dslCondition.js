/** Shared helpers for «Если» / «Если не» DSL conditions (studio layer). */

export const DSL_COMPARE_OPS = Object.freeze([
  '==', '!=', '>=', '<=', '>', '<', 'содержит', 'начинается_с', 'в',
]);

export function isConditionLikeType(type) {
  return type === 'condition' || type === 'condition_not';
}

/** `текст == "да"` → `текст не == "да"` */
export function negateConditionForDsl(cond) {
  const raw = String(cond || '').trim();
  if (!raw) return raw;
  for (const op of DSL_COMPARE_OPS) {
    const needle = ` ${op} `;
    const idx = raw.indexOf(needle);
    if (idx >= 0) {
      const left = raw.slice(0, idx).trimEnd();
      const right = raw.slice(idx + needle.length).trimStart();
      if (/\sне\s*$/u.test(left)) return raw;
      return `${left} не ${op} ${right}`;
    }
  }
  if (/^\s*не\s+/iu.test(raw)) return raw;
  return `не ${raw}`;
}

/** Parse body of `если …:` into condition / condition_not blocks. */
export function parseIfConditionFromDsl(inner) {
  const body = String(inner || '').trim().replace(/:?\s*$/, '');
  const negRe = /^(.+?)\s+не\s+(==|!=|>=|<=|>|<|содержит|начинается_с|в)\s+(.+)$/u;
  const m = body.match(negRe);
  if (m) {
    return {
      type: 'condition_not',
      props: { cond: `${m[1].trim()} ${m[2]} ${m[3].trim()}` },
    };
  }
  return { type: 'condition', props: { cond: body } };
}
