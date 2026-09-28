const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const t = require("@babel/types");
const generate = require("@babel/generator").default;
const fs = require("node:fs");
const vm = require("node:vm");

const code = fs.readFileSync('./captcha-sdk.min.js', 'utf-8');
const ast = parser.parse(code, {sourceType:"script"});
let stringArray = [];
let rotateCode = "";
let arrayFunctionCode = "";
let decodeFunctionCode = "";
const decodeBindings = new Set();

traverse(ast, {
    NumberLiteral(path) {
        delete path.node.extra;
    },
    StringLiteral(path) {
        delete path.node.extra;
    },
    VariableDeclarator(path) {
        if (
            t.isIdentifier(path.node.init, { name: "_0x6805" }) &&
            t.isIdentifier(path.node.id)
        ) {
            const binding = path.scope.getBinding(path.node.id.name);

            if (binding) {
                decodeBindings.add(binding);
            }
        }
        if (!t.isIdentifier(path.node.id, {name:"_0x1d9928"})) return;
        if (!t.isArrayExpression(path.node.init)) return;
        stringArray = path.node.init.elements.map(i=>i.value);
    },
    FunctionDeclaration(path) {
        if (t.isIdentifier(path.node.id, {name:"_0x468a"})) arrayFunctionCode = generate(path.node).code;
        if (!t.isIdentifier(path.node.id, {name:"_0x6805"})) return;
        decodeFunctionCode = generate(path.node).code;
    },
    CallExpression(path) {
        if (!t.isFunctionExpression(path.node.callee)) return;
        if (!t.isIdentifier(path.node.arguments[0], {name:"_0x468a"})) return;    
        console.log("找到旋转函数调用:");
        rotateCode = generate(path.node).code;
        
    }
})




// 1. 先定义两个函数，最后执行旋转调用
const setupCode = [
    arrayFunctionCode,
    decodeFunctionCode,
    `(${rotateCode});`
].join("\n");

// 2. 创建执行环境
const context = vm.createContext({});

// 3. 执行拼好的代码，完成数组旋转
vm.runInContext(setupCode, context, {
    timeout: 1000
});

// 4. 用旋转后的数组查一个字符串
const result = vm.runInContext("_0x6805(0x7aa)", context);

traverse(ast, {
    CallExpression(path) {
        // 只处理通过名字调用的函数
        if (!t.isIdentifier(path.node.callee)) return;

        const binding = path.scope.getBinding(path.node.callee.name);

        // 必须是之前收集的别名，而且没有被重新赋值
        if (!decodeBindings.has(binding)) return;
        if (!binding.constant) return;

        // 暂时只处理一个数字参数
        const args = path.node.arguments;
        if (args.length !== 1 || !t.isNumericLiteral(args[0])) return;

        // 旋转调用内部不能替换，它依赖旋转过程中的数组状态
        if (path.findParent(parent =>
            parent.isCallExpression() &&
            t.isFunctionExpression(parent.node.callee) &&
            t.isIdentifier(parent.node.arguments[0], { name: "_0x468a" })
        )) return;

        const result = vm.runInContext(
            `_0x6805(${args[0].value})`,
            context,
            { timeout: 1000 }
        );

        if (typeof result !== "string") return;

        // 用字符串节点替换整个调用
        path.replaceWith(t.stringLiteral(result));
    }
});

// 保存结果
fs.writeFileSync(
    "./practice/3.output.js",
    generate(ast).code,
    "utf8"
);

console.log(result); // 应该输出：function
console.log();
console.log("保存的别名数量：", decodeBindings.size);
