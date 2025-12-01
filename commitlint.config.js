module.exports = {
    extends: ['@commitlint/config-conventional'],
    rules: {
        'type-enum': [2, 'always', ['feature', 'feat', 'fix', 'chore', 'docs', 'style', 'refactor']],
        'subject-case': [0, 'never', []]
    }
};