/** @type {import('tailwindcss').Config} */
const primary = "#f29545";
const primaryLight = "#fdedd7";

module.exports = {
    content: ["templates/**/*.html"],
    theme: {
        extend: {
            colors: {
                //TODO: Rename to gray when primary color is picked
                primary: {
                    DEFAULT: "#515864",
                    50: "#f4f5f7",
                    100: "#e4e7e9",
                    200: "#ccd0d5",
                    300: "#a8afb8",
                    400: "#7c8794",
                    500: "#616b79",
                    600: "#515864",
                    700: "#484d56",
                    800: "#3f434b",
                    900: "#383b41",
                    950: "#232429",
                },
                accent: "#ff7000",
                placeholder: {
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
            },
        },
    },
    plugins: [],
};
