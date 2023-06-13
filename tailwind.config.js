/** @type {import('tailwindcss').Config} */
const primary = "#649d9d";
const primaryLight = "#8cbcba";
const primaryDark = "#4a8182";

module.exports = {
    content: ["templates/**/*.html"],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: primary,
                    light: primaryLight,
                    dark: primaryDark,
                    50: "#f4f9f9",
                    100: "#dcebea",
                    200: "#a7cecb",
                    300: "#8cbcba",
                    400: "#649d9d",
                    500: "#4a8182",
                    600: "#3a6667",
                    700: "#315354",
                    800: "#2a4445",
                    900: "#263b3b",
                    950: "#122021",
                },
            },
        },
    },
    plugins: [],
};
