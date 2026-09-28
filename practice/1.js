const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;
const t = require("@babel/types")
const generate = require("@babel/generator").default;
const fs = require("node:fs")

const code = fs.readFileSync('./captcha-sdk.min.js', "utf-8");
const ast = parser.parse(code, {sourceType: "script"});

const arr = [];
const result = Object.create(null);

traverse(ast, {
    FunctionExpression(path) {
        if (!t.isIdentifier(path.node.id, {name: "_0x2134e2"})) return;
        console.log("找到函数:", path.node.id.name);
        path.traverse({
            AssignmentExpression(innerPath) {
                const { left, right } = innerPath.node;

                // 1. 左侧必须是属性访问
                if (!t.isMemberExpression(left)) {
                    return;
                }

                // 2. 只收集 _0x4410af 的属性
                if (!t.isIdentifier(left.object, { name: "_0x4410af" })) {
                    return;
                }

                // 3. 提取键名
                let key;

                if (!left.computed) {
                    // 对象.属性
                    key = left.property.name;
                } else if (t.isStringLiteral(left.property)) {
                    // 对象['属性']
                    key = left.property.value;
                } else {
                    // 对象[函数调用等表达式]
                    // 还不知道真实键名，暂时用表达式作为标签
                    key = `[${generate(left.property).code}]`;
                }

                // 4. 提取右侧源码
                const value = generate(right).code;

                // 5. 存入对象
                result[key] = value;
            }
        })
    }

})


console.log(result);
