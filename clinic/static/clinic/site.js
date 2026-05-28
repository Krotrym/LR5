function setupServiceFilter() {
    const grid = document.querySelector("#serviceGrid");
    const search = document.querySelector("#serviceSearch");
    const category = document.querySelector("#categoryFilter");
    const sort = document.querySelector("#sortSelect");
    if (!grid || !search || !category || !sort) return;

    const cards = Array.from(grid.querySelectorAll(".service-card"));

    function applyFilters() {
        const query = search.value.trim().toLowerCase();
        const selectedCategory = category.value;
        const sorted = [...cards].sort((a, b) => {
            if (sort.value === "price-asc") return Number(a.dataset.price) - Number(b.dataset.price);
            if (sort.value === "price-desc") return Number(b.dataset.price) - Number(a.dataset.price);
            if (sort.value === "duration") return Number(a.dataset.duration) - Number(b.dataset.duration);
            return a.dataset.name.localeCompare(b.dataset.name, "ru");
        });

        sorted.forEach((card) => {
            const textMatch = card.dataset.name.includes(query) || card.dataset.description.includes(query);
            const categoryMatch = !selectedCategory || card.dataset.category === selectedCategory;
            card.hidden = !(textMatch && categoryMatch);
            grid.appendChild(card);
        });
    }

    [search, category, sort].forEach((element) => element.addEventListener("input", applyFilters));
    applyFilters();
}

function setupBirthDateValidation() {
    const form = document.querySelector("[data-registration-form]");
    if (!form) return;
    const input = form.querySelector('input[name="birth_date"]');
    if (!input) return;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    input.max = today.toISOString().slice(0, 10);

    function parseDate(value) {
        if (!value) return null;
        const isoMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (isoMatch) return new Date(Number(isoMatch[1]), Number(isoMatch[2]) - 1, Number(isoMatch[3]));
        const ruMatch = value.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
        if (ruMatch) return new Date(Number(ruMatch[3]), Number(ruMatch[2]) - 1, Number(ruMatch[1]));
        return null;
    }

    function getAge(date) {
        let age = today.getFullYear() - date.getFullYear();
        const monthDelta = today.getMonth() - date.getMonth();
        if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < date.getDate())) age -= 1;
        return age;
    }

    function validateBirthDate(showMessage) {
        input.setCustomValidity("");
        const value = parseDate(input.value);
        if (!value) return true;

        const age = getAge(value);
        const isInvalid = value > today || age < 14 || age > 120;
        if (isInvalid) {
            input.setCustomValidity("Введите корректную дату рождения: возраст от 14 до 120 лет.");
            if (showMessage) input.reportValidity();
            return false;
        }
        return true;
    }

    input.addEventListener("input", () => validateBirthDate(false));
    input.addEventListener("change", () => validateBirthDate(false));

    form.addEventListener("submit", (event) => {
        if (!validateBirthDate(true)) event.preventDefault();
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupServiceFilter();
    setupBirthDateValidation();
});
