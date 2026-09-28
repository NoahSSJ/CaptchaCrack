const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const t = require("@babel/types");
const generate = require("@babel/generator").default;
const fs = require("node:fs");


const code = fs.readFileSync('samples\\captcha-sdk.min.js', 'utf-8');
const ast = parser.parse(code, {sourceType:"script"});
let arrayFunctionCode = '';
let rotateFuntionCode = '';
let decodeFunctionCode = '';
let decodeFuncNameBindings = new Set();

traverse(ast, {
    NumberLiteral(path) {
        delete path.node.extra;
    },
    StringLiteral(path) {
        delete path.node.extra;
    },
    FunctionDeclaration(path) {
        if (t.isIdentifier(path.node.id, {name:"_0x468a"})) {
            arrayFunctionCode = generate(path.node).code;
            // console.log("数组函数为:", arrayFunctionCode);
        }
        
            
        if (t.isIdentifier(path.node.id, {name:"_0x6805"}))
            decodeFunctionCode = generate(path.node).code
    },
    FunctionExpression(path) {
        if (t.isIdentifier(path.node.id, {name:"_0x513725"})) {
            console.log(path.node.id);
            
        }
    },
    CallExpression(path) {
        if (t.isFunctionExpression(path.node.callee) && t.isIdentifier(path.node.arguments[0], {name:"_0x468a"})) {
            rotateFuntionCode = generate(path.node).code;
        }
    },
    // AssignmentExpression(path) {
    //     if (path.node.operator === "=" && t.isMemberExpression(path.node.left) && t.isFunctionExpression(path.node.right)) {
    //         console.log(path.node.toString());
    //     }
    // },
    VariableDeclarator(path) {
        if (t.isIdentifier(path.node.id) && t.isIdentifier(path.node.init, {name:"_0x6805"})) {
            const binding = path.scope.getBinding(path.node.id.name);
            if (binding) {
                console.log(binding.identifier.name);
                decodeFuncNameBindings.add(binding);
            }
        }
    }
})

while (true) {
    const previousSize = decodeFuncNameBindings.size;
    traverse(ast, {
        VariableDeclarator(path) {
            if (!t.isIdentifier(path.node.id))
                return;
            if (!t.isIdentifier(path.node.init))
                return;
            const sourceBinding = path.scope.getBinding(
                path.node.init.name
            );

            if (!decodeFuncNameBindings.has(sourceBinding))
                return;
            if (!sourceBinding.constant)
                return;
            const binding = path.scope.getBinding(path.node.id.name);
            if (binding && binding.constant) {
                decodeFuncNameBindings.add(binding);
            }
        }
    })
    if (decodeFuncNameBindings.size == previousSize)
        break
}
console.log("收集后的别名总数：", decodeFuncNameBindings.size);