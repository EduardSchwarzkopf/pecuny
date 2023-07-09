/** @type {import('tailwindcss').Config} */
const primary = "#4f46f8";
const primaryLight = "#5357ff";

module.exports = {
    content: ["templates/**/*.html"],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: primary,
                    light: primaryLight,
                    50: "#ecf1ff",
                    100: "#dce5ff",
                    200: "#c1ceff",
                    300: "#9baeff",
                    400: "#7382ff",
                    500: "#5357ff",
                    600: "#4f46f8",
                    700: "#3427db",
                    800: "#2a23b0",
                    900: "#27248b",
                    950: "#191551",
                },
                gray: {
                    DEFAULT: "#668091",
                    50: "#f9fafb",
                    100: "#eceff2",
                    200: "#d5dde2",
                    300: "#b0bfc9",
                    400: "#859bab",
                    500: "#668091",
                    600: "#516778",
                    700: "#425462",
                    800: "#394753",
                    900: "#333e47",
                    950: "#22292f",
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
                    light: "#f0fdf4",
                    DEFAULT: "#85f0aa",
                    dark: "#49df7d",
                    hover: "#bbf7cf",
                    50: "#f0fdf4",
                    100: "#dcfce6",
                    200: "#baf8cf",
                    300: "#85f0aa",
                    400: "#49df7e",
                    500: "#20c75b",
                    600: "#15a448",
                    700: "#14813b",
                    800: "#156633",
                    900: "#13542c",
                    950: "#052e15",
                },
                warning: {
                    light: "#fffaeb",
                    DEFAULT: "#ffe08a",
                    dark: "#ffc94a",
                    hover: "#fff0c6",
                },
            },
        },
    },
    plugins: [],
};
