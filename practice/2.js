const parser = require('@babel/parser');
const traverse = require("@babel/traverse").default;
const t = require("@babel/types");
const generate = require("@babel/generator").default;
const fs = require("node:fs");

const code = fs.readFileSync('./captcha-sdk.min.js', 'utf-8');
const ast = parser.parse(code, {sourceType: "script"});
let stringArray = [];

traverse(ast, {
    NumberLiteral(path) {
        // console.log(path.node);
        delete path.node.extra;
    },
    StringLiteral(path) {
        // console.log(path.node);
        delete path.node.extra;
    },
    FunctionDeclaration(path) {
        if (!t.isIdentifier(path.node.id ,{name:"_0x6805"})) return;
        console.log("找到函数:", path.node.id.name);
        
    },
    VariableDeclarator(path) {
        if (!t.isIdentifier(path.node.id, {name:"_0x1d9928"})) return;
        if (!t.isArrayExpression(path.node.init)) return;
        // console.log(path.node.init);
        stringArray = path.node.init.elements.map(i=>i.value)
        // console.log(stringArray);
    }
})

// newCode = generate(ast).code;
// console.log(newCode);
