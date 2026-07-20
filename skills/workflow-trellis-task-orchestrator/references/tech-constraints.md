# 技术约束专项

按技术栈/场景分类，编排器根据任务类型自动注入对应约束。

---

## RESEARCH_CODE 约束（PISFM / 科研项目）

```
## 环境约束
- 操作系统：WSL2 Ubuntu 22.04
- GPU：RTX 5060（Blackwell 架构，sm_120）
- CUDA：12.8
- Python：>= 3.10（建议 3.11）
- PyTorch：2.x（需手动编译 causal-conv1d 和 mamba-ssm）
- 激活环境命令：source ~/envs/pisfm/bin/activate

## 代码规范
- 模型结构：BiMamba 编码器，双向 SSM
- 数据集：LUCAS、Forest SOC（光谱预处理后）
- 光谱波段：需经 spectral_preprocessing.py 处理后才能输入模型
- 标签：SOC（土壤有机碳），单位 g/kg
- 超参数：统一用 YAML 配置文件管理（configs/），禁止硬编码

## 实验规范
- 每次实验前：记录 baseline 到 journal
- 每次改动模型：先用 10 条随机样本验证 forward pass shape
- NaN 处理：检查 scaler 是否匹配（训练/推理用同一个 scaler 实例）
- 结果记录：metrics 字典写入 results/[experiment-name].json

## 禁止事项
- 禁止在主分支跑破坏性实验（用 git worktree 隔离）
- 禁止直接 pip install 未经验证的包（RTX 5060 有兼容性问题）
- 禁止在训练脚本中 print 大量中间值（用 logging 模块）
```

---

## FREELANCE 约束（Spring Boot + Vue 外包）

```
## 后端技术栈
- Java 17 + Spring Boot 3.x
- MyBatis-Plus 3.x（禁止写原生 SQL，除复杂查询）
- MySQL 8（字符集 utf8mb4）
- Redis（缓存、Session）
- 统一响应封装：Result<T>（code / msg / data）
- 统一异常处理：GlobalExceptionHandler

## 分层规范
- Controller：只做参数校验 + 调用 Service，禁止业务逻辑
- Service：业务逻辑，禁止直接调 Mapper（通过 IService 接口）
- Mapper：数据访问，禁止业务判断
- Entity：对应数据库表，禁止有业务方法
- DTO/VO：请求/响应对象，与 Entity 分离

## 前端技术栈
- Vue 3 + Vite
- Element Plus（UI 组件库）
- Axios（封装为 request.js，统一处理 token 和错误）
- Pinia（状态管理）
- Vue Router 4（路由守卫处理权限）

## 安全约束
- 接口权限：用 Sa-Token 或 Spring Security 注解控制
- SQL 注入：全部用 MyBatis-Plus，禁止字符串拼接 SQL
- XSS：前端 v-html 禁止直接渲染用户输入
- 密码：BCrypt 加密，禁止明文存储

## 接口规范
- RESTful 风格：GET/POST/PUT/DELETE
- 路径：/api/v1/[模块]/[资源]
- 分页：统一 Page<T> 返回，入参 pageNum/pageSize
```

---

## 通用 Python 约束

```
## 代码风格
- 格式化：black（line-length = 88）
- lint：flake8 / ruff
- 类型检查：pyright（strict 模式）
- 文档字符串：Google 风格

## 依赖管理
- 使用 requirements.txt 或 pyproject.toml 管理
- 新增依赖须注释用途
- 版本固定（不用 >=，用 ==）

## 测试
- 测试框架：pytest
- 覆盖率：核心模块 >= 80%
- 测试文件：tests/test_[module_name].py
```

---

## 通用 Git 约束

```
## Commit 规范
格式：<type>(<scope>): <subject>
类型：feat / fix / refactor / test / docs / chore / style

示例：
feat(model): add bidirectional mamba encoder
fix(preprocessing): handle NaN in LUCAS dataset scaler
refactor(api): split user controller into auth and profile

## 分支规范
- main：稳定版本，禁止直接 push
- feature/[task-slug]：新功能
- fix/[bug-slug]：Bug 修复
- experiment/[exp-name]：科研实验（用 git worktree）
```
