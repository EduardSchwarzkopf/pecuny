/** @type {import('tailwindcss').Config} */
const primary = "#f29545";
const primaryLight = "#fdedd7";

module.exports = {
    content: ["templates/**/*.html"],
    theme: {
        extend: {
            colors: {
                accent: "#ff7000",
                primary: {
                    DEFAULT: primary,
                    light: primaryLight,
                    50: "#fef7ee",
                    100: "#fdedd7",
                    200: "#fad8ae",
                    300: "#f7bc7a",
                    400: "#f29545",
                    500: "#ee7721",
                    600: "#e05d16",
                    700: "#b94715",
                    800: "#943918",
                    900: "#773017",
                    950: "#40170a",
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
