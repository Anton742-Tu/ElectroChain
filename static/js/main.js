// Основные функции для сайта

$(document).ready(function() {
    // Инициализация всплывающих подсказок
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Автоматическое скрытие сообщений через 5 секунд
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Подтверждение удаления
    $('.confirm-delete').on('click', function(e) {
        if (!confirm('Вы уверены, что хотите удалить этот элемент?')) {
            e.preventDefault();
        }
    });
});

// Функция для форматирования даты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Функция для форматирования валюты
function formatCurrency(amount) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'RUB',
        minimumFractionDigits: 2
    }).format(amount);
}