import axios from 'axios';
import dotenv from 'dotenv';
import { Question } from './database.js';

dotenv.config();

// 支持多种大模型API
interface LLMConfig {
    provider: 'openai' | 'anthropic' | 'ollama' | 'zhipu';
    apiKey?: string;
    baseUrl?: string;
    model: string;
}

// 从环境变量读取配置
const LLM_CONFIG: LLMConfig = {
    provider: (process.env.LLM_PROVIDER as any) || 'zhipu',
    apiKey: process.env.LLM_API_KEY,
    baseUrl: process.env.LLM_BASE_URL || 'https://open.bigmodel.cn/api/paas/v4/',
    model: process.env.LLM_MODEL || 'glm-4'
};

export interface AnswerEvaluation {
    score: number; // 0-100分
    feedback: string;
    strengths: string[];
    improvements: string[];
    correctnessLevel: 'correct' | 'partially_correct' | 'incorrect';
    detailedAnalysis: string;
}

/**
 * 使用大模型评判用户答案
 */
export async function evaluateAnswer(
    question: Question,
    userAnswer: string
): Promise<AnswerEvaluation> {
    try {
        const prompt = buildEvaluationPrompt(question, userAnswer);
        
        switch (LLM_CONFIG.provider) {
            case 'zhipu':
                return await evaluateWithZhipu(prompt);
            case 'openai':
                return await evaluateWithOpenAI(prompt);
            case 'ollama':
                return await evaluateWithOllama(prompt);
            default:
                throw new Error(`不支持的LLM提供商: ${LLM_CONFIG.provider}`);
        }
    } catch (error) {
        console.error('评判答案时出错:', error);
        return {
            score: 0,
            feedback: '评判服务暂时不可用，请稍后重试。',
            strengths: [],
            improvements: ['请检查网络连接或联系管理员'],
            correctnessLevel: 'incorrect',
            detailedAnalysis: '无法完成评判分析'
        };
    }
}

/**
 * 构建评判提示词
 */
function buildEvaluationPrompt(question: Question, userAnswer: string): string {
    return `你是一位专业的学科教师，请根据以下信息对学生的答案进行评判：

题目信息：
- 标题：${question.title}
- 描述：${question.description}
- 科目：${question.subject}
- 难度：${question.difficulty}
- 图片描述：${question.imageDescription || '无图片'}
- 参考答案：${question.referenceAnswer}

学生答案：
${userAnswer}

请按照以下JSON格式返回评判结果：
{
    "score": 85,
    "feedback": "整体回答较好，主要知识点掌握正确...",
    "strengths": ["知识点理解正确", "逻辑清晰"],
    "improvements": ["计算过程可以更详细", "注意单位换算"],
    "correctnessLevel": "partially_correct",
    "detailedAnalysis": "详细的分析说明..."
}

评判标准：
1. 准确性 (40%): 答案是否正确
2. 完整性 (30%): 是否包含所有要求的要点
3. 逻辑性 (20%): 推理过程是否清晰
4. 表达 (10%): 语言表达是否规范

correctnessLevel字段说明：
- "correct": 答案完全正确
- "partially_correct": 答案部分正确
- "incorrect": 答案错误

请确保返回有效的JSON格式。`;
}

/**
 * 使用智谱AI进行评判
 */
async function evaluateWithZhipu(prompt: string): Promise<AnswerEvaluation> {
    if (!LLM_CONFIG.apiKey) {
        throw new Error('智谱AI API密钥未配置');
    }

    const response = await axios.post(
        `${LLM_CONFIG.baseUrl}chat/completions`,
        {
            model: LLM_CONFIG.model,
            messages: [
                {
                    role: 'user',
                    content: prompt
                }
            ],
            temperature: 0.3,
            max_tokens: 2000
        },
        {
            headers: {
                'Authorization': `Bearer ${LLM_CONFIG.apiKey}`,
                'Content-Type': 'application/json'
            }
        }
    );

    const content = response.data.choices[0].message.content;
    return parseEvaluationResponse(content);
}

/**
 * 使用OpenAI进行评判
 */
async function evaluateWithOpenAI(prompt: string): Promise<AnswerEvaluation> {
    if (!LLM_CONFIG.apiKey) {
        throw new Error('OpenAI API密钥未配置');
    }

    const response = await axios.post(
        `${LLM_CONFIG.baseUrl || 'https://api.openai.com/v1/'}chat/completions`,
        {
            model: LLM_CONFIG.model,
            messages: [
                {
                    role: 'user',
                    content: prompt
                }
            ],
            temperature: 0.3,
            max_tokens: 2000
        },
        {
            headers: {
                'Authorization': `Bearer ${LLM_CONFIG.apiKey}`,
                'Content-Type': 'application/json'
            }
        }
    );

    const content = response.data.choices[0].message.content;
    return parseEvaluationResponse(content);
}

/**
 * 使用Ollama进行评判（本地部署）
 */
async function evaluateWithOllama(prompt: string): Promise<AnswerEvaluation> {
    const response = await axios.post(
        `${LLM_CONFIG.baseUrl || 'http://localhost:11434/api/'}generate`,
        {
            model: LLM_CONFIG.model,
            prompt: prompt,
            stream: false
        }
    );

    const content = response.data.response;
    return parseEvaluationResponse(content);
}

/**
 * 解析大模型返回的评判结果
 */
function parseEvaluationResponse(content: string): AnswerEvaluation {
    try {
        // 尝试提取JSON部分
        const jsonMatch = content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            const parsed = JSON.parse(jsonMatch[0]);
            return {
                score: Math.max(0, Math.min(100, parsed.score || 0)),
                feedback: parsed.feedback || '无法生成反馈',
                strengths: Array.isArray(parsed.strengths) ? parsed.strengths : [],
                improvements: Array.isArray(parsed.improvements) ? parsed.improvements : [],
                correctnessLevel: ['correct', 'partially_correct', 'incorrect'].includes(parsed.correctnessLevel) 
                    ? parsed.correctnessLevel : 'incorrect',
                detailedAnalysis: parsed.detailedAnalysis || '无详细分析'
            };
        }
    } catch (error) {
        console.error('解析评判结果失败:', error);
    }

    // 如果解析失败，返回基础评判
    return {
        score: 60,
        feedback: content.substring(0, 500) || '收到回答，但无法完成详细评判',
        strengths: ['提供了答案'],
        improvements: ['建议参考标准答案进行对比'],
        correctnessLevel: 'partially_correct',
        detailedAnalysis: '系统无法解析详细评判结果，建议人工核查'
    };
}

/**
 * 获取答题建议
 */
export async function getAnsweringSuggestions(question: Question): Promise<string> {
    try {
        const prompt = `作为学科教师，请为以下题目提供答题建议和解题思路：

题目：${question.title}
描述：${question.description}
科目：${question.subject}
难度：${question.difficulty}
图片描述：${question.imageDescription || '无图片'}

请提供：
1. 解题思路和方法
2. 需要注意的关键点
3. 常见错误提醒
4. 答题建议

请用简洁明了的语言回答，帮助学生更好地理解和解答这道题目。`;

        // 使用配置的LLM获取建议
        switch (LLM_CONFIG.provider) {
            case 'zhipu':
                const response = await axios.post(
                    `${LLM_CONFIG.baseUrl}chat/completions`,
                    {
                        model: LLM_CONFIG.model,
                        messages: [{ role: 'user', content: prompt }],
                        temperature: 0.7,
                        max_tokens: 1000
                    },
                    {
                        headers: {
                            'Authorization': `Bearer ${LLM_CONFIG.apiKey}`,
                            'Content-Type': 'application/json'
                        }
                    }
                );
                return response.data.choices[0].message.content;
            default:
                return '答题建议服务暂时不可用，请根据题目描述和参考答案自行分析。';
        }
    } catch (error) {
        console.error('获取答题建议失败:', error);
        return '获取答题建议时出错，请稍后重试。';
    }
}
