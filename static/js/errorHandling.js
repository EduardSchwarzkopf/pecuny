// errorHandling.js
function hideError(input) {
    const errorDiv = input.parentElement.querySelector(".field-error");
    if (errorDiv) {
        errorDiv.style.display = "none";
    }
}
