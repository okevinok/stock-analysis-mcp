# 题库MCP服务

一个基于Model Context Protocol (MCP)的智能题库系统，支持随机出题、AI评判答案和学习建议。

## 功能特性

### 🎯 核心功能
- **随机出题**: 从题库中随机获取题目，支持按科目和难度筛选
- **图片支持**: 题目可包含图片和图片描述信息
- **AI评判**: 使用大模型对用户答案进行智能评判和分析
- **学习建议**: 提供个性化的答题建议和解题思路
- **多科目支持**: 数学、物理、化学、英语等多个学科

### 🤖 AI评判功能
- **多维度评分**: 从准确性、完整性、逻辑性、表达等方面评判
- **详细反馈**: 提供具体的优点分析和改进建议
- **多模型支持**: 支持智谱AI、OpenAI、Ollama等多种大模型

## 快速开始

### 1. 环境配置

复制环境变量模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置大模型API：
```env
# 智谱AI配置（推荐）
LLM_PROVIDER=zhipu
LLM_API_KEY=your_zhipu_api_key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4
```

### 2. 安装依赖
```bash
npm install
```

### 3. 构建项目
```bash
npm run build
```

### 4. 启动服务

开发模式：
```bash
npm run dev:question-bank
```

生产模式：
```bash
npm run start:question-bank
```

## 可用工具

### 📚 题目管理

#### `get-random-question`
获取随机题目
- `subject` (可选): 指定科目（数学、物理、化学、英语）
- `difficulty` (可选): 指定难度（easy、medium、hard）

#### `get-question-by-id`
根据ID获取指定题目
- `id` (必填): 题目ID

#### `show-current-question`
显示当前活跃的题目

### 📝 答题评判

#### `submit-answer`
提交答案并获取AI评判
- `answer` (必填): 用户的答案
- `questionId` (可选): 题目ID，不提供则使用当前题目

#### `get-answering-suggestions`
获取答题建议和解题思路
- `questionId` (可选): 题目ID，不提供则使用当前题目

### 📊 统计信息

#### `get-database-stats`
获取题库统计信息，包括题目总数、科目分布、难度分布等

## 使用示例

### 1. 获取随机数学题
```json
{
  "tool": "get-random-question",
  "arguments": {
    "subject": "数学",
    "difficulty": "medium"
  }
}
```

### 2. 提交答案
```json
{
  "tool": "submit-answer",
  "arguments": {
    "answer": "对称轴为x=2，顶点坐标为(2, -1)，函数解析式为y = (x-2)² - 1"
  }
}
```

### 3. 获取答题建议
```json
{
  "tool": "get-answering-suggestions",
  "arguments": {}
}
```

## AI评判示例

系统会从以下维度对答案进行评判：

```json
{
  "score": 85,
  "feedback": "整体回答较好，主要知识点掌握正确，但计算过程可以更详细。",
  "strengths": [
    "正确识别了二次函数的关键特征",
    "逻辑思路清晰"
  ],
  "improvements": [
    "建议写出更详细的计算步骤",
    "注意检查最终答案的格式"
  ],
  "correctnessLevel": "partially_correct",
  "detailedAnalysis": "学生正确理解了二次函数的基本概念..."
}
```

## 题库数据结构

题目包含以下字段：
- `id`: 题目唯一标识
- `title`: 题目标题
- `description`: 题目描述
- `imageUrl`: 题目图片URL（可选）
- `imageDescription`: 图片内容描述（可选）
- `referenceAnswer`: 参考答案
- `difficulty`: 难度等级（easy/medium/hard）
- `subject`: 所属科目
- `tags`: 标签列表

## 支持的大模型

### 智谱AI (推荐)
```env
LLM_PROVIDER=zhipu
LLM_API_KEY=your_api_key
LLM_MODEL=glm-4
```

### OpenAI
```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxxxxxxxx
LLM_MODEL=gpt-3.5-turbo
```

### Ollama (本地部署)
```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434/api/
LLM_MODEL=llama3
```

## 扩展功能

### 添加新题目
修改 `src/database.ts` 中的 `questionsDatabase` 数组来添加新题目。

### 自定义评判标准
修改 `src/llmEvaluator.ts` 中的评判提示词来调整评判标准。

### 集成真实数据库
可以将 `src/database.ts` 中的内存数据库替换为MySQL、PostgreSQL等真实数据库。

## 注意事项

1. **API密钥安全**: 请妥善保管您的大模型API密钥
2. **网络连接**: 确保服务器能够访问大模型API
3. **图片资源**: 确保题目中的图片URL可以正常访问
4. **性能考虑**: 大模型API调用可能需要一定时间，请适当设置超时

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `.env` 文件中的API密钥是否正确
   - 确认API密钥有足够的调用余额

2. **网络连接问题**
   - 检查网络连接是否正常
   - 确认是否需要代理设置

3. **评判结果异常**
   - 检查大模型返回的格式是否正确
   - 查看控制台错误日志

### 日志调试
启动服务时会在stderr输出日志信息，可以用于调试：
```bash
npm run dev:question-bank 2>debug.log
```

## 许可证

本项目采用 ISC 许可证。
