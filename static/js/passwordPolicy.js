document.addEventListener("DOMContentLoaded", (event) => {
    const passwordField = document.getElementById("password");
    const passwordConfirmField = document.getElementById("password_confirm");
    const submitButton = document.getElementById("submit");

    const passwordConfirmErrorDiv = document.getElementById(
        "password_confirm_error"
    );
    const passwordPolicyDiv = document.getElementById("password_policy");
    const passwordPolicy = {
        length: document.getElementById("password_length"),
        uppercase: document.getElementById("password_uppercase"),
        lowercase: document.getElementById("password_lowercase"),
        digit: document.getElementById("password_digit"),
        special: document.getElementById("password_special"),
    };

    function checkPasswordPolicy(password) {
        const policies = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            digit: /[0-9]/.test(password),
            special: /[!@#$%^&*()]/.test(password),
        };

        for (const policy in policies) {
            if (policies[policy]) {
                passwordPolicy[policy].classList.remove("text-danger");
                passwordPolicy[policy].classList.add("text-success-dark");
            } else {
                passwordPolicy[policy].classList.remove("text-success-dark");
                passwordPolicy[policy].classList.add("text-danger");
            }
        }

        for (const policy in policies) {
            if (!policies[policy]) {
                return false;
            }
        }

        return true;
    }

    function comparePasswords() {
        const password = passwordField.value;
        const passwordConfirm = passwordConfirmField.value;
        const policyPassed = checkPasswordPolicy(password);
        if (password !== passwordConfirm) {
            passwordConfirmErrorDiv.style.display = "block";
            passwordConfirmErrorDiv.textContent = "Passwords do not match.";
            submitButton.disabled = true;
        } else {
            passwordConfirmErrorDiv.style.display = "none";
            submitButton.disabled = !policyPassed;
        }
    }

    passwordField.addEventListener("input", function () {
        passwordPolicyDiv.style.display = "block";
        const password = passwordField.value;
        const policyPassed = checkPasswordPolicy(password);
        submitButton.disabled = !policyPassed;
        if (policyPassed) {
            comparePasswords();
        }
    });

    passwordConfirmField.addEventListener("input", comparePasswords);
});
