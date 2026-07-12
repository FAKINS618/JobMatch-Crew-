# Docker 与部署知识

## Docker 基础
考察点：是否理解镜像、容器和部署一致性。

回答要点：
- 镜像是应用和运行环境的打包结果。
- 容器是镜像运行后的实例。
- Docker 可以减少“本地能跑、服务器不能跑”的环境差异。

项目追问：
- FastAPI + Streamlit 项目如何拆容器？
- `.env` 中的 API Key 为什么不应该写进镜像？

## Dockerfile 常见指令
考察点：是否理解容器构建流程。

回答要点：
- `FROM` 指定基础镜像。
- `WORKDIR` 指定工作目录。
- `COPY` 拷贝项目文件。
- `RUN` 安装依赖。
- `CMD` 指定容器启动命令。

项目追问：
- FastAPI 后端容器启动命令如何写？
- Streamlit 前端容器启动命令如何写？

## docker-compose
考察点：是否理解多服务编排。

回答要点：
- docker-compose 用于同时启动多个服务。
- 后续项目可以拆成 backend、frontend、redis、vector-db。
- compose 适合本地开发和演示部署。

项目追问：
- 如果异步任务升级为 Redis + RQ，compose 里需要哪些服务？
- SQLite 是否适合容器化部署？有什么限制？

## 部署注意点
考察点：是否理解真实上线时的基础风险。

回答要点：
- API Key 放在环境变量或部署平台 Secret 中。
- 生产环境不应开启过多 verbose 日志，避免泄露简历和 JD。
- 用户简历属于隐私数据，数据库和日志都需要注意脱敏。
