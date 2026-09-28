const parser = require("@babel/parser")
const traverse = require("@babel/traverse").default
const t = require("@babel/types")
const generate = require('@babel/generator').default
const fs = require("node:fs")

const code = fs.readFileSync("./captcha-sdk.min.js", "utf-8")
// console.log(code);

const ast = parser.parse(code, {sourceType: "script"})

traverse(ast, {
    NumberLiteral(path) {
        // console.log(path.node);
        // console.log("16进制:", path.node.extra.raw, '-> 数字:', path.node.value);
        delete path.node.extra.raw
    },
    CallExpression(path) {
        if (t.isIdentifier(path.node.callee, {name:"_0x2134e2"})) {
            console.log("调用的函数名:", path.node.callee);
            console.log(path.node)
        }
    },
    FunctionExpression(path) {
        if (!t.isIdentifier(path.node.id, { name: "_0x2134e2" })) return;
        console.log("函数名:", path.node.id.name);
        console.log("函数节点:", path.node);
        path.traverse({
            Function(innerPath) {
                innerPath.skip()
            },
            AssignmentExpression(assignPath) {
                const { left, right } = assignPath.node;

                if (
                    !t.isMemberExpression(left) ||
                    !t.isIdentifier(left.object, { name: "_0x4410af" })
                ) {
                    return;
                }

                const key = left.computed
                    ? t.isStringLiteral(left.property)
                        ? left.property.value
                        : `[${generate(left.property).code}]`
                    : left.property.name;

                console.log(`${key}: ${generate(right).code}`);
            }
        })



    }
})

newCode = generate(ast).code
// console.log(newCode);
