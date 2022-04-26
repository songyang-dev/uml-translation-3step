import { parse, parseFile, formatters } from 'plantuml-parser';

// Example PlantUML
const data = `
@startuml
!theme plain
    class Node 
    {
    }
    Node "0" --> "1" Node: inNode
@enduml
`;

// parse PlantUML
const result = parse(data);

// Format and print parse result
console.log(
    formatters.default(result)
);