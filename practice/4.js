const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const t = require("@babel/types")
const generate = require("@babel/generator").default;
const fs = require("node:fs");
const vm = require("node:vm");

const code = fs.readFileSync('captcha-sdk.min.js', 'utf-8');
const ast = parser.parse(code, {sourceType: "script"});
let arrayFunctionCode = '';
let rotateFuntionCode = '';
let decodeFunctionCode = '';
const decodeFuncNameBindings = new Set();

traverse(ast, {
    NumberLiteral(path) {
        delete path.node.extra;
    },
    StringLiteral(path) {
        delete path.node.extra;
    },
    FunctionDeclaration(path) {
        if (t.isIdentifier(path.node.id, {name:"_0x468a"})) {
            console.log("找到数组函数:", path.node.id.name);
            arrayFunctionCode = generate(path.node).code;
            // console.log(arrayFunctionCode);
        }
        if (t.isIdentifier(path.node.id, {name:"_0x6805"})) {
            console.log("找到解码函数:", path.node.id.name);
            decodeFunctionCode = generate(path.node).code;
            // console.log(decodeFunctionCode);
        }
    },
    CallExpression(path) {
        if (t.isFunctionExpression(path.node.callee) && t.isIdentifier(path.node.arguments[0], {name:"_0x468a"})) {
            console.log("找到旋转数组函数:", path.node.id);
            rotateFuntionCode = generate(path.node).code;
            // console.log(rotateFuntionCode);
        }
    },
    VariableDeclarator(path) {
        if (t.isIdentifier(path.node.id) && t.isIdentifier(path.node.init, {name:"_0x6805"})) {
            const binding = path.scope.getBinding(path.node.id.name);
            if (binding) {
                // console.log(binding);
                
                decodeFuncNameBindings.add(binding);
            }
        }

    }
})


let previousSize;

do {
    previousSize = decodeFuncNameBindings.size;
    traverse(ast, {
        VariableDeclarator(path) {
            if (!t.isIdentifier(path.node.id)) return;
            if (!t.isIdentifier(path.node.init)) return;

            // 右边是不是已经记录过的别名？
            const sourceBinding = path.scope.getBinding(
                path.node.init.name
            );

            if (!decodeFuncNameBindings.has(sourceBinding)) return;
            if (!sourceBinding.constant) return;

            // 如果是，就把左边也记录下来
            const binding = path.scope.getBinding(path.node.id.name);

            if (binding && binding.constant) {
                decodeFuncNameBindings.add(binding);
            }
        }
    });
} while (decodeFuncNameBindings.size > previousSize);

console.log("收集后的别名总数：", decodeFuncNameBindings.size);

// console.log(decodeFuncNameBindings);
