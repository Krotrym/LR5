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
    input.max = today.toISOString().slice(0, 10);

    form.addEventListener("submit", (event) => {
        const value = input.value ? new Date(`${input.value}T00:00:00`) : null;
        if (!value) return;

        let age = today.getFullYear() - value.getFullYear();
        const monthDelta = today.getMonth() - value.getMonth();
        if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < value.getDate())) age -= 1;

        if (value > today || age < 14 || age > 120) {
            input.setCustomValidity("Введите корректную дату рождения: возраст от 14 до 120 лет.");
            input.reportValidity();
            event.preventDefault();
        } else {
            input.setCustomValidity("");
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupServiceFilter();
    setupBirthDateValidation();
});
