const fs = require('fs');
const path = require('path');

const TOPICS = [
    { id: 'arrays', name: 'Arrays & Searching' },
    { id: 'linked-lists', name: 'Linked Lists' },
    { id: 'stacks', name: 'Stacks & Queues' },
    { id: 'trees', name: 'Trees & BST' },
    { id: 'sorting', name: 'Sorting Algorithms' },
    { id: 'graphs', name: 'Graphs & BFS/DFS' },
    { id: 'hash-tables', name: 'Hash Tables' },
    { id: 'dynamic-programming', name: 'Dynamic Programming' },
    { id: 'heaps', name: 'Heaps & Priority Queues' },
    { id: 'tries', name: 'Tries (Prefix Trees)' }
];

const quizzes = {};

TOPICS.forEach(topic => {
    const questions = [];
    for (let i = 1; i <= 30; i++) {
        let diff = 'Easy';
        if (i > 10) diff = 'Medium';
        if (i > 20) diff = 'Hard';

        let q = '';
        let options = [];
        let answer = 0;
        let explanation = '';

        if (diff === 'Easy') {
            q = `What is a fundamental characteristic of ${topic.name} (Concept ${i})?`;
            options = ['It uses O(1) space', 'It organizes data efficiently', 'It is never used in practice', 'It only works with numbers'];
            answer = 1;
            explanation = `Understanding the basics of ${topic.name} is crucial for solving easy problems.`;
        } else if (diff === 'Medium') {
            q = `In a standard implementation of ${topic.name}, which operation takes O(log n) time? (Variation ${i})`;
            options = ['Insertion at head', 'Searching for a specific node/element', 'Deleting all elements', 'Reversing the structure'];
            answer = 1;
            explanation = `Many intermediate DSA structures like ${topic.name} optimize searching or insertion into logarithmic time bounds.`;
        } else {
            q = `Consider a complex system utilizing ${topic.name}. How do you resolve edge-case collisions or worst-case degradation? (Scenario ${i})`;
            options = ['Use a brute-force approach instead', 'Rely on randomized partition or tree-balancing', 'Increase memory limit to infinity', 'Ignore it safely'];
            answer = 1;
            explanation = `Hard problems in ${topic.name} usually require balancing, amortization, or randomized pivots to avoid O(n^2) or O(n) degradation.`;
        }

        questions.push({
            id: i,
            difficulty: diff,
            q,
            options,
            answer,
            explanation
        });
    }
    quizzes[topic.id] = questions;
});

const fileContent = `export const QUIZZES = ${JSON.stringify(quizzes, null, 4)};\n`;

const outputPath = path.join(__dirname, 'quizzes.js');
fs.writeFileSync(outputPath, fileContent);
console.log(`Generated quizzes.js at ${outputPath} with 300 questions.`);
