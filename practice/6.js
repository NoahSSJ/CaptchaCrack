const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const t = require("@babel/types");
const generate = require("@babel/generator").default;
const fs = require("node:fs");
const path = require("node:path");

const input = path.resolve(__dirname, "../samples/greenseer.js");
const output = path.resolve(__dirname, "6.output.js");
const ast = parser.parse(fs.readFileSync(input, "utf8"), { sourceType: "script" });
const arrays = {};
let found = false;

// 只接受常量值；!0、!1 转换为布尔字面量。
function constantNode(node) {
    if (t.isStringLiteral(node) || t.isNumericLiteral(node) ||
        t.isBooleanLiteral(node) || t.isNullLiteral(node)) {
        return t.cloneNode(node, true);
    }
    if (t.isUnaryExpression(node, { operator: "!" }) &&
        t.isNumericLiteral(node.argument)) {
        return t.booleanLiteral(!node.argument.value);
    }
    throw new Error(`不支持的数组元素类型：${node?.type}`);
}

traverse(ast, {
    CallExpression(callPath) {
        const { callee, arguments: args } = callPath.node;
        if (!t.isFunctionExpression(callee)) return;
        if (callPath.getFunctionParent()) return;
        if (callee.params.length !== 6 || args.length !== 6) return;
        if (!callee.params.every(param => t.isIdentifier(param))) return;
        if (!args.every(arg => t.isArrayExpression(arg))) return;

        found = true;
        const functionPath = callPath.get("callee");
        const replacements = [];

        callee.params.forEach((param, index) => {
            arrays[param.name] = args[index];
            const values = args[index].elements.map(constantNode);
            const binding = functionPath.scope.getBinding(param.name);
            if (!binding.constant) {
                throw new Error(`参数 ${param.name} 被重新赋值，不能直接替换`);
            }

            // 只获取此参数的引用，排除内部作用域中的同名变量。
            for (const reference of binding.referencePaths) {
                const member = reference.parentPath;
                if (!member.isMemberExpression() || reference.key !== "object" ||
                    !member.node.computed || !t.isNumericLiteral(member.node.property)) {
                    throw new Error(`${param.name} 存在非固定索引访问，需要单独分析`);
                }
                // 检查全部引用后再替换，避免把写入操作当作读取。
                if (!member.isReferenced() || member.parentPath.isUpdateExpression() ||
                    member.parentPath.isUnaryExpression({ operator: "delete" })) {
                    throw new Error(`${param.name} 存在数组写入操作，不能直接替换`);
                }
                const offset = member.node.property.value;
                if (!Number.isInteger(offset) || offset < 0 || offset >= values.length) {
                    throw new Error(`${param.name}[${offset}] 索引越界`);
                }
                replacements.push({ member, value: values[offset] });
            }
            console.log(`${param.name}: ${values.length} 个元素，${binding.referencePaths.length} 处引用`);
        });

        for (const { member, value } of replacements) {
            member.replaceWith(t.cloneNode(value, true));
        }
        console.log(`共替换 ${replacements.length} 处数组访问`);
        callPath.stop();
    }
});

if (!found) throw new Error("未找到接收六个数组的最外层自执行函数");

// 保留原来的形参和实参数组，只替换读取表达式。
const result = generate(ast, { comments: true }).code;
parser.parse(result, { sourceType: "script" });
fs.writeFileSync(output, result, "utf8");
console.log(`已保存：${output}`);
