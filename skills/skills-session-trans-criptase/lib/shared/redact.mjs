// 敏感信息脱敏：trans_status / trans_code_status / trans_code_config_check / doctor.mjs 统一调用，
// 杜绝到处手写"只显示末 4 位"这类逻辑、避免遗漏导致 key 泄露。
export function redactSecret(value) {
    if (!value) return '(未设置)'
    const s = String(value)
    if (s.length <= 4) return '****'
    return `${'*'.repeat(Math.max(0, s.length - 4))}${s.slice(-4)}`
}

/** 返回配置的展示安全版本：apiKey 等敏感字段脱敏，其余原样透传。 */
export function redactConfigForDisplay(cfg) {
    if (!cfg || typeof cfg !== 'object') return cfg
    const out = { ...cfg }
    if ('apiKey' in out) out.apiKey = out.apiKey ? redactSecret(out.apiKey) : '(未设置)'
    if ('apiKeySet' in out === false && 'apiKey' in cfg) out.apiKeySet = !!cfg.apiKey
    return out
}
