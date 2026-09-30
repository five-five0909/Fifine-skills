// Node 22 的内置 fetch（undici）不读 http_proxy/https_proxy，
// 必须经代理出网的机器上所有外网 fetch 都会 failed。
// 用法：NODE_OPTIONS="--import file:///<本文件路径>" node ...
// Node >= 24 无需本文件：直接用 NODE_OPTIONS=--use-env-proxy。
// 依赖：本文件同级或任意祖先目录的 node_modules/undici；缺失时仅告警，不改变进程行为。
try {
    const { EnvHttpProxyAgent, setGlobalDispatcher } = await import('undici')
    setGlobalDispatcher(new EnvHttpProxyAgent())
} catch (error) {
    console.warn('[fifine-skills] undici 未安装，跳过代理注入：', error.message)
}
