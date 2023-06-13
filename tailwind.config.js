/** @type {import('tailwindcss').Config} */
const primary = "#ff9c5f";
const primaryLight = "#ffaf7e";
const primaryDark = "#fe7839";

module.exports = {
    content: ["templates/**/*.html"],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: primary,
                    light: primaryLight,
                    dark: primaryDark,
                    50: "#fff5ed",
                    100: "#ffe7d4",
                    200: "#ffaf7e",
                    300: "#ff9c5f",
                    400: "#fe7839",
                    500: "#fc5413",
                    600: "#ed3909",
                    700: "#c52809",
                    800: "#9c2110",
                    900: "#7e1e10",
                    950: "#440c06",
                },
                info: {
                    light: "#c7def0",
                    DEFAULT: "#5ca2d4",
                    dark: "#3886bf",
                    hover: "#95c1e4",
                },
                danger: {
                    light: "#fdced5",
                    DEFAULT: "#f14668",
                    dark: "#dd214f",
                    hover: "#f8748b",
                },
                success: {
                    light: "#dcfce6",
                    DEFAULT: "#85f0aa",
                    dark: "#49df7d",
                    hover: "#bbf7cf",
                },
                warning: {
                    light: "#fffaeb",
                    DEFAULT: "#ffe08a",
                    dark: "#ffc94a",
                    hover: "#fff0c6",
                },
                dark: {
                    light: "gray-50",
                    DEFAULT: "gray-800",
                    dark: "gray-300",
                    hover: "gray-200",
                },
            },
        },
    },
    plugins: [],
};
