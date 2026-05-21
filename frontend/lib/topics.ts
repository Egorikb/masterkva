// Topic to Image mapping for DeepTutor
// Maps grade + topic to appropriate textbook page

export interface TopicImage {
  topic: string;
  grade: number;
  page: string;
  description: string;
}

export const topicImages: TopicImage[] = [
  // Grade 1
  { topic: "numbers", grade: 1, page: "019", description: "Счёт 1-10" },
  { topic: "addition", grade: 1, page: "094", description: "Сложение (CPA)" },
  { topic: "subtraction", grade: 1, page: "094", description: "Вычитание (CPA)" },
  { topic: "geometry", grade: 1, page: "034", description: "Геометрия" },
  
  // Grade 2
  { topic: "numbers", grade: 2, page: "001", description: "Счёт 1-100" },
  { topic: "addition", grade: 2, page: "045", description: "Сложение 2 знач." },
  { topic: "subtraction", grade: 2, page: "045", description: "Вычитание 2 знач." },
  { topic: "geometry", grade: 2, page: "034", description: "Геометрия" },
  
  // Grade 3
  { topic: "numbers", grade: 3, page: "001", description: "Счёт 1-1000" },
  { topic: "addition", grade: 3, page: "045", description: "Сложение 3 знач." },
  { topic: "subtraction", grade: 3, page: "045", description: "Вычитание 3 знач." },
  { topic: "geometry", grade: 3, page: "034", description: "Геометрия" },
  
  // Grade 4
  { topic: "numbers", grade: 4, page: "001", description: "Многозначные" },
  { topic: "addition", grade: 4, page: "045", description: "Сложение" },
  { topic: "subtraction", grade: 4, page: "045", description: "Вычитание" },
  { topic: "geometry", grade: 4, page: "034", description: "Геометрия" },
  
  // Grade 5
  { topic: "numbers", grade: 5, page: "001", description: "Дроби" },
  { topic: "addition", grade: 5, page: "045", description: "Сложение дробей" },
  { topic: "geometry", grade: 5, page: "034", description: "Геометрия" },
  
  // Grade 6
  { topic: "numbers", grade: 6, page: "001", description: "Проценты" },
  { topic: "addition", grade: 6, page: "045", description: "Действия" },
  { topic: "geometry", grade: 6, page: "034", description: "Геометрия" },
];

// Get image URL for grade + topic
export function getImageUrl(grade: number, topic: string): string {
  const mapping = topicImages.find(t => t.grade === grade && t.topic === topic);
  const page = mapping?.page || "094";
  return `/api/images/${grade}/${page}`;
}

// Get available topics for grade
export function getTopicsForGrade(grade: number): string[] {
  const topics = topicImages.filter(t => t.grade === grade);
  return [...new Set(topics.map(t => t.topic))];
}

export default { topicImages, getImageUrl, getTopicsForGrade };
