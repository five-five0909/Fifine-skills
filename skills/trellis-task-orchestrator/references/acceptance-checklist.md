# 验收 Checklist 大全

对应 `/trellis:finish-work` 的执行内容，按任务类型细化。

---

## 通用 Checklist（所有类型都要跑）

```
## 通用验收
- [ ] git status 确认无意外的改动文件
- [ ] git diff 阅读本次所有变更，理解改动范围
- [ ] 没有遗留 TODO / FIXME（或已创建对应 task）
- [ ] 没有注释掉的废弃代码块
- [ ] 没有硬编码的路径/密钥/用户名
```

---

## NEW_FEATURE 专项

```
## 功能验收
- [ ] 核心功能在目标环境（dev/prod）手动验证通过
- [ ] 边界条件测试：空输入、最大值、异常输入
- [ ] 错误处理：异常有合适的错误信息

## 代码质量
- [ ] lint 无报错：flake8 / eslint / pylint（视语言）
- [ ] type-check 无报错：pyright / tsc
- [ ] 单元测试全部通过：pytest / vitest
- [ ] 新增代码有对应测试覆盖

## 文档
- [ ] 新增 public API / 函数有 docstring / JSDoc
- [ ] README 若有影响则已更新
- [ ] .trellis/spec/ 若有新约定则已 update-spec

## Spec 对照
- [ ] /trellis:check 输出无违规项
- [ ] 未引入 spec 中禁止的新依赖
```

---

## BUG_FIX 专项

```
## 修复验收
- [ ] 原错误场景不再复现
- [ ] 相关功能回归测试通过
- [ ] 错误日志中不再出现对应报错

## 代码质量
- [ ] lint / type-check 无报错
- [ ] 未用 try/except 掩盖根本问题
- [ ] 修复范围最小（未引入不必要的改动）

## 文档
- [ ] 若是高频 Bug，已在 .trellis/spec/ 中记录防范规范
```

---

## REFACTOR 专项

```
## 重构验收
- [ ] 所有原有单元测试通过（行为不变）
- [ ] 外部接口签名不变，或有明确迁移说明
- [ ] 无新引入的技术债

## 质量指标
- [ ] 代码行数/函数复杂度有实质下降（或结构更清晰）
- [ ] 循环引用消除
- [ ] 命名更符合 spec 规范

## lint / type-check / test 全通过
```

---

## RESEARCH_CODE 专项

```
## 实验验收
- [ ] forward pass shape 验证通过（所有 tensor shape 符合预期）
- [ ] loss 无 NaN / Inf（用 torch.isnan / torch.isinf 检查）
- [ ] 在小数据集（≤ 100 条）跑通完整 pipeline
- [ ] 指标与 baseline 对比有记录

## 代码质量
- [ ] 实验超参数用配置文件管理（非硬编码）
- [ ] 随机种子固定（torch.manual_seed / numpy.random.seed）
- [ ] GPU 显存无泄漏（torch.cuda.empty_cache 在适当位置调用）

## 记录
- [ ] 实验结果记录到 .trellis/workspace/[user]/experiments/
- [ ] journal 更新：做了什么、结果如何、下一步计划
```

---

## FREELANCE 专项

```
## 后端验收
- [ ] 所有 API 接口用 Postman/curl 验证通过
- [ ] 接口返回格式符合约定（统一 Result 封装）
- [ ] 数据库操作无 N+1 查询
- [ ] 敏感接口有权限校验

## 前端验收
- [ ] 目标浏览器（Chrome 最新版）手动点击所有功能
- [ ] 表单校验：必填、格式、长度限制
- [ ] 接口错误有友好提示（非直接展示后端报错）
- [ ] 列表页有分页/空状态处理

## 交付物
- [ ] README.md 包含：环境要求、启动步骤、账号信息
- [ ] SQL 建表语句（schema.sql）与当前数据库一致
- [ ] 无测试账号信息硬编码在代码中
```
