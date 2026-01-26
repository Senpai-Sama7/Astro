// Example plugin tools
module.exports = {
  greet: async (input) => {
    const name = input.name || 'World';
    return { message: `Hello, ${name}!`, timestamp: new Date().toISOString() };
  },

  reverse: async (input) => {
    const text = input.text || '';
    return { original: text, reversed: text.split('').reverse().join('') };
  }
};
