import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import dotenv from "dotenv";
import { 
    getRandomQuestion, 
    getQuestionById, 
    getQuestionsBySubject, 
    getQuestionsByDifficulty,
    getAllSubjects,
    getDatabaseStats,
    Question 
} from "./database.js";
import { evaluateAnswer, getAnsweringSuggestions } from "./llmEvaluator.js";

// Load environment variables
dotenv.config();

// Create an MCP server
const server = new McpServer({
    name: "question-bank-mcp",
    version: "1.0.0"
});

// 用于存储当前会话的题目（简单的内存存储）
let currentQuestion: Question | null = null;

// Add a resource for question data
server.resource(
    "question-data",
    new ResourceTemplate("question://{id}", { list: undefined }),
    async (uri, { id }) => {
        try {
            const questionId = parseInt(id as string);
            const question = getQuestionById(questionId);
            
            if (!question) {
                throw new Error(`题目 ID ${id} 不存在`);
            }

            const questionData = {
                id: question.id,
                title: question.title,
                description: question.description,
                subject: question.subject,
                difficulty: question.difficulty,
                tags: question.tags,
                imageUrl: question.imageUrl,
                imageDescription: question.imageDescription,
                hasImage: !!question.imageUrl
            };

            return {
                contents: [{
                    uri: uri.href,
                    text: JSON.stringify(questionData, null, 2),
                    mimeType: "application/json"
                }]
            };
        } catch (error) {
            throw new Error(`获取题目数据失败: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
);

// Tool: 获取随机题目
server.tool(
    "get-random-question",
    {
        subject: z.string().optional().describe("指定科目（可选），如：数学、物理、化学、英语"),
        difficulty: z.enum(["easy", "medium", "hard"]).optional().describe("指定难度（可选）：easy（简单）、medium（中等）、hard（困难）")
    },
    async ({ subject, difficulty }) => {
        try {
            let question: Question;
            
            if (subject && difficulty) {
                // 根据科目和难度筛选
                const questions = getQuestionsBySubject(subject).filter(q => q.difficulty === difficulty);
                if (questions.length === 0) {
                    return {
                        content: [{ type: "text", text: `没有找到科目为"${subject}"且难度为"${difficulty}"的题目` }],
                        isError: true
                    };
                }
                question = questions[Math.floor(Math.random() * questions.length)];
            } else if (subject) {
                // 仅根据科目筛选
                const questions = getQuestionsBySubject(subject);
                if (questions.length === 0) {
                    return {
                        content: [{ type: "text", text: `没有找到科目为"${subject}"的题目` }],
                        isError: true
                    };
                }
                question = questions[Math.floor(Math.random() * questions.length)];
            } else if (difficulty) {
                // 仅根据难度筛选
                const questions = getQuestionsByDifficulty(difficulty);
                question = questions[Math.floor(Math.random() * questions.length)];
            } else {
                // 完全随机
                question = getRandomQuestion();
            }

            // 保存当前题目到会话
            currentQuestion = question;

            const result = formatQuestionForDisplay(question);
            return {
                content: [{ type: "text", text: result }]
            };
        } catch (error) {
            return {
                content: [{ type: "text", text: `获取题目失败: ${error instanceof Error ? error.message : String(error)}` }],
                isError: true
            };
        }
    }
);

// Tool: 根据ID获取指定题目
server.tool(
    "get-question-by-id",
    {
        id: z.number().describe("题目ID")
    },
    async ({ id }) => {
        try {
            const question = getQuestionById(id);
            if (!question) {
                return {
                    content: [{ type: "text", text: `题目 ID ${id} 不存在` }],
                    isError: true
                };
            }

            // 保存当前题目到会话
            currentQuestion = question;

            const result = formatQuestionForDisplay(question);
            return {
                content: [{ type: "text", text: result }]
            };
        } catch (error) {
            return {
                content: [{ type: "text", text: `获取题目失败: ${error instanceof Error ? error.message : String(error)}` }],
                isError: true
            };
        }
    }
);

// Tool: 提交答案并获取评判
server.tool(
    "submit-answer",
    {
        answer: z.string().describe("用户的答案"),
        questionId: z.number().optional().describe("题目ID（可选，如果不提供则使用当前题目）")
    },
    async ({ answer, questionId }) => {
        try {
            let question: Question | null = null;

            if (questionId) {
                question = getQuestionById(questionId);
                if (!question) {
                    return {
                        content: [{ type: "text", text: `题目 ID ${questionId} 不存在` }],
                        isError: true
                    };
                }
            } else if (currentQuestion) {
                question = currentQuestion;
            } else {
                return {
                    content: [{ type: "text", text: "请先获取一道题目，或指定题目ID" }],
                    isError: true
                };
            }

            if (!answer.trim()) {
                return {
                    content: [{ type: "text", text: "请提供您的答案" }],
                    isError: true
                };
            }

            // 使用大模型评判答案
            const evaluation = await evaluateAnswer(question, answer);

            const result = formatEvaluationResult(question, answer, evaluation);
            return {
                content: [{ type: "text", text: result }]
            };
        } catch (error) {
            return {
                content: [{ type: "text", text: `评判答案失败: ${error instanceof Error ? error.message : String(error)}` }],
                isError: true
            };
        }
    }
);

// Tool: 获取答题建议
server.tool(
    "get-answering-suggestions",
    {
        questionId: z.number().optional().describe("题目ID（可选，如果不提供则使用当前题目）")
    },
    async ({ questionId }) => {
        try {
            let question: Question | null = null;

            if (questionId) {
                question = getQuestionById(questionId);
                if (!question) {
                    return {
                        content: [{ type: "text", text: `题目 ID ${questionId} 不存在` }],
                        isError: true
                    };
                }
            } else if (currentQuestion) {
                question = currentQuestion;
            } else {
                return {
                    content: [{ type: "text", text: "请先获取一道题目，或指定题目ID" }],
                    isError: true
                };
            }

            const suggestions = await getAnsweringSuggestions(question);
            
            const result = `📝 **答题建议**

**题目**: ${question.title}

${suggestions}

---
💡 **提示**: 这些建议仅供参考，请根据题目要求独立思考和作答。`;

            return {
                content: [{ type: "text", text: result }]
            };
        } catch (error) {
            return {
                content: [{ type: "text", text: `获取答题建议失败: ${error instanceof Error ? error.message : String(error)}` }],
                isError: true
            };
        }
    }
);

// Tool: 获取题库统计信息
server.tool(
    "get-database-stats",
    {},
    async () => {
        try {
            const stats = getDatabaseStats();
            const subjects = getAllSubjects();

            const result = `📊 **题库统计信息**

**总题目数量**: ${stats.totalQuestions}

**按科目分布**:
${Object.entries(stats.bySubject).map(([subject, count]) => `• ${subject}: ${count}题`).join('\n')}

**按难度分布**:
${Object.entries(stats.byDifficulty).map(([difficulty, count]) => {
    const difficultyName = difficulty === 'easy' ? '简单' : difficulty === 'medium' ? '中等' : '困难';
    return `• ${difficultyName}: ${count}题`;
}).join('\n')}

**可用科目**: ${subjects.join('、')}

---
🎯 使用 \`get-random-question\` 工具获取题目，使用 \`submit-answer\` 提交答案获取评判。`;

            return {
                content: [{ type: "text", text: result }]
            };
        } catch (error) {
            return {
                content: [{ type: "text", text: `获取统计信息失败: ${error instanceof Error ? error.message : String(error)}` }],
                isError: true
            };
        }
    }
);

// Tool: 显示当前题目
server.tool(
    "show-current-question",
    {},
    async () => {
        try {
            if (!currentQuestion) {
                return {
                    content: [{ type: "text", text: "当前没有活跃的题目。请使用 `get-random-question` 或 `get-question-by-id` 获取题目。" }]
                };
            }

            const result = formatQuestionForDisplay(currentQuestion);
            return {
                content: [{ type: "text", text: result }]
            };
        } catch (error) {
            return {
                content: [{ type: "text", text: `显示当前题目失败: ${error instanceof Error ? error.message : String(error)}` }],
                isError: true
            };
        }
    }
);

/**
 * 格式化题目显示
 */
function formatQuestionForDisplay(question: Question): string {
    const difficultyEmoji = question.difficulty === 'easy' ? '🟢' : question.difficulty === 'medium' ? '🟡' : '🔴';
    const difficultyText = question.difficulty === 'easy' ? '简单' : question.difficulty === 'medium' ? '中等' : '困难';

    let result = `📚 **第${question.id}题** | ${question.subject} | ${difficultyEmoji} ${difficultyText}

**题目**: ${question.title}

**题目描述**:
${question.description}`;

    if (question.imageUrl) {
        result += `\n\n🖼️ **图片**: ${question.imageUrl}`;
    }

    if (question.imageDescription) {
        result += `\n\n📋 **图片描述**: ${question.imageDescription}`;
    }

    if (question.tags && question.tags.length > 0) {
        result += `\n\n🏷️ **标签**: ${question.tags.join('、')}`;
    }

    result += `\n\n---
💭 **提示**: 
• 请仔细阅读题目和图片描述
• 使用 \`submit-answer\` 工具提交您的答案
• 使用 \`get-answering-suggestions\` 获取答题建议
• 答案将由AI进行评判并给出详细反馈`;

    return result;
}

/**
 * 格式化评判结果
 */
function formatEvaluationResult(question: Question, userAnswer: string, evaluation: any): string {
    const scoreEmoji = evaluation.score >= 90 ? '🌟' : evaluation.score >= 80 ? '👍' : evaluation.score >= 60 ? '👌' : '💪';
    const levelEmoji = evaluation.correctnessLevel === 'correct' ? '✅' : 
                      evaluation.correctnessLevel === 'partially_correct' ? '⚠️' : '❌';

    let result = `🎯 **答案评判结果**

**题目**: ${question.title}

**您的答案**:
${userAnswer}

**评判结果**:
${scoreEmoji} **得分**: ${evaluation.score}/100 ${levelEmoji}

**整体反馈**:
${evaluation.feedback}`;

    if (evaluation.strengths && evaluation.strengths.length > 0) {
        result += `\n\n✨ **优点**:
${evaluation.strengths.map((s: string) => `• ${s}`).join('\n')}`;
    }

    if (evaluation.improvements && evaluation.improvements.length > 0) {
        result += `\n\n🔧 **改进建议**:
${evaluation.improvements.map((i: string) => `• ${i}`).join('\n')}`;
    }

    result += `\n\n📖 **详细分析**:
${evaluation.detailedAnalysis}`;

    result += `\n\n📚 **参考答案**:
${question.referenceAnswer}`;

    result += `\n\n---
🎉 继续加油！使用 \`get-random-question\` 获取下一题练习。`;

    return result;
}

async function main() {
    try {
        // Create a transport for stdio communication
        const transport = new StdioServerTransport();

        // Connect the server to the transport
        await server.connect(transport);

        console.error("Question Bank MCP Server running on stdio");
    } catch (error) {
        console.error("Error starting server:", error);
        process.exit(1);
    }
}

main();
