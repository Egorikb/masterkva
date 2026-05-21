import { NextResponse } from 'next/server';

const TOPICS = [
  { id: 1, name: 'Числа 1-10', grade: 1, description: 'Счёт от 1 до 10', topic: 'numbers_1_10' },
  { id: 2, name: 'Числа 11-20', grade: 1, description: 'Счёт от 11 до 20', topic: 'numbers_11_20' },
  { id: 3, name: 'Геометрия', grade: 1, description: 'Фигуры и формы', topic: 'geometry' },
  { id: 4, name: 'Сложение', grade: 1, description: 'Сложение чисел', topic: 'addition' },
  { id: 5, name: 'Вычитание', grade: 1, description: 'Вычитание чисел', topic: 'subtraction' },
  { id: 6, name: 'Метод CPA', grade: 1, description: 'Конкретное-Образное-Абстрактное', topic: 'cpa' },
  { id: 7, name: 'Часы и время', grade: 1, description: 'Определение времени', topic: 'time' },
  { id: 8, name: 'Позиция', grade: 1, description: 'Положение предметов', topic: 'position' },
  { id: 9, name: 'Повторение', grade: 0, description: 'Проверка знаний', topic: 'review' },
];

export async function GET() {
  return NextResponse.json({ topics: TOPICS });
}
