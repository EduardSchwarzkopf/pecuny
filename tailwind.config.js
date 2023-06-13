/** @type {import('tailwindcss').Config} */
const primary = "#a7cecb";
const primaryLight = "#dcebea";

module.exports = {
    content: ["templates/**/*.html"],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: primary,
                    50: "#f4f9f9",
                    100: primaryLight,
                    light: primaryLight,
                    200: primary,
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
