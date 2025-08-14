// 模拟数据库 - 题库数据
export interface Question {
    id: number;
    title: string;
    description: string;
    imageUrl?: string;
    imageDescription?: string;
    referenceAnswer: string;
    difficulty: 'easy' | 'medium' | 'hard';
    subject: string;
    tags: string[];
    createdAt: Date;
}

// 模拟题库数据
const questionsDatabase: Question[] = [
    {
        id: 1,
        title: "二次函数的图像分析",
        description: "观察图像中的二次函数图像，请分析该函数的对称轴、顶点坐标，并写出函数的解析式。",
        // 使用简单的ASCII图示意
        imageUrl: "data:text/plain;base64," + Buffer.from(`
        y
        |
        |     *
        |   *   *
        | *       *
        |*         *
        +---+---+---+--- x
            2
        `).toString('base64'),
        imageDescription: "图像显示一个开口向上的抛物线，顶点在(2, -1)，经过点(0, 3)和(4, 3)",
        referenceAnswer: "对称轴为x=2，顶点坐标为(2, -1)，函数解析式为y = (x-2)² - 1 或 y = x² - 4x + 3",
        difficulty: 'medium',
        subject: '数学',
        tags: ['二次函数', '图像分析', '解析式'],
        createdAt: new Date('2024-01-01')
    },
    {
        id: 2,
        title: "三角形相似判定",
        description: "根据图中给出的两个三角形，判断它们是否相似，并说明理由。如果相似，求出相似比。",
        imageUrl: "https://example.com/similar-triangles.png",
        imageDescription: "图像显示两个三角形ABC和DEF，其中角A=角D=60°，AB=6，AC=8，DE=9，DF=12",
        referenceAnswer: "两个三角形相似。理由：角A=角D=60°，且AB/DE = AC/DF = 6/9 = 8/12 = 2/3，满足SAS相似判定定理。相似比为2:3。",
        difficulty: 'medium',
        subject: '数学',
        tags: ['三角形', '相似', '几何'],
        createdAt: new Date('2024-01-02')
    },
    {
        id: 3,
        title: "物理电路分析",
        description: "分析图中的串并联电路，计算总电阻和各支路电流。已知电源电压为12V。",
        imageUrl: "https://example.com/circuit-diagram.png",
        imageDescription: "电路图显示一个混联电路，包含三个电阻：R1=4Ω串联，然后与R2=6Ω和R3=3Ω的并联部分串联",
        referenceAnswer: "R2和R3并联等效电阻为2Ω，总电阻为4+2=6Ω，总电流为12V/6Ω=2A，通过R1的电流为2A，R2支路电流为1A，R3支路电流为2A",
        difficulty: 'hard',
        subject: '物理',
        tags: ['电路', '串并联', '欧姆定律'],
        createdAt: new Date('2024-01-03')
    },
    {
        id: 4,
        title: "化学方程式配平",
        description: "配平图中所示的化学反应方程式，并说明反应类型。",
        imageUrl: "https://example.com/chemical-equation.png",
        imageDescription: "显示铝与氧气反应生成氧化铝的化学方程式：Al + O₂ → Al₂O₃",
        referenceAnswer: "4Al + 3O₂ → 2Al₂O₃，这是化合反应（氧化反应）",
        difficulty: 'easy',
        subject: '化学',
        tags: ['化学方程式', '配平', '化合反应'],
        createdAt: new Date('2024-01-04')
    },
    {
        id: 5,
        title: "英语语法分析",
        description: "分析句子结构，指出句子成分和语法点。",
        imageUrl: "https://example.com/sentence-structure.png",
        imageDescription: "句子：'The book that I bought yesterday is very interesting.' 需要分析定语从句结构",
        referenceAnswer: "主句：'The book is very interesting'，定语从句：'that I bought yesterday'修饰'book'，关系代词'that'在从句中作宾语",
        difficulty: 'medium',
        subject: '英语',
        tags: ['定语从句', '语法分析', '句子结构'],
        createdAt: new Date('2024-01-05')
    }
];

/**
 * 获取随机题目
 */
export function getRandomQuestion(): Question {
    const randomIndex = Math.floor(Math.random() * questionsDatabase.length);
    return questionsDatabase[randomIndex];
}

/**
 * 根据ID获取题目
 */
export function getQuestionById(id: number): Question | undefined {
    return questionsDatabase.find(question => question.id === id);
}

/**
 * 根据科目筛选题目
 */
export function getQuestionsBySubject(subject: string): Question[] {
    return questionsDatabase.filter(question => 
        question.subject.toLowerCase() === subject.toLowerCase()
    );
}

/**
 * 根据难度筛选题目
 */
export function getQuestionsByDifficulty(difficulty: 'easy' | 'medium' | 'hard'): Question[] {
    return questionsDatabase.filter(question => question.difficulty === difficulty);
}

/**
 * 获取所有科目列表
 */
export function getAllSubjects(): string[] {
    const subjects = questionsDatabase.map(q => q.subject);
    return [...new Set(subjects)];
}

/**
 * 添加新题目（模拟数据库插入）
 */
export function addQuestion(question: Omit<Question, 'id' | 'createdAt'>): Question {
    const newQuestion: Question = {
        ...question,
        id: Math.max(...questionsDatabase.map(q => q.id)) + 1,
        createdAt: new Date()
    };
    questionsDatabase.push(newQuestion);
    return newQuestion;
}

/**
 * 获取题库统计信息
 */
export function getDatabaseStats() {
    const subjects = getAllSubjects();
    const difficulties = ['easy', 'medium', 'hard'] as const;
    
    const stats = {
        totalQuestions: questionsDatabase.length,
        bySubject: {} as Record<string, number>,
        byDifficulty: {} as Record<string, number>
    };

    subjects.forEach(subject => {
        stats.bySubject[subject] = getQuestionsBySubject(subject).length;
    });

    difficulties.forEach(difficulty => {
        stats.byDifficulty[difficulty] = getQuestionsByDifficulty(difficulty).length;
    });

    return stats;
}
