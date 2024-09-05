let products = {
    products: [],
    sets: []
};
let currentCategory = 'products';
let cart = {};

async function getProducts() {
    try {
        const response = await fetch(`api/products/?category=${currentCategory}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        products[currentCategory] = data.map(product => ({
            id: product.id,
            name: product.product_name,
            description: product.description_ru,
            price: product.price,
            image: product.product_image
        }));
        renderProducts();
    } catch (error) {
        console.error('Ошибка при получении продуктов:', error);
    }
}

function renderProducts() {
    const productList = document.getElementById('product-list');
    productList.innerHTML = '';
    products[currentCategory].forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'product-card';
        productCard.innerHTML = `
            <img src="${product.image}" alt="${product.name}" class="product-image">
            <div class="product-info">
                <h2>${product.name}</h2>
                <p>Цена: ${product.price} сум</p>
                <button onclick="showProductDetails(${product.id})">Подробнее</button>
                <div class="quantity-control">
                    ${renderQuantityControl(product.id)}
                </div>
            </div>
        `;
        productList.appendChild(productCard);
    });
}

function renderQuantityControl(productId) {
    const quantity = cart[productId] ? cart[productId].quantity : 0;
    if (quantity === 0) {
        return `<button onclick="addToCart(${productId})">Добавить в корзину</button>`;
    } else {
        return `
            <button onclick="decreaseQuantity(${productId})">-</button>
            <span>${quantity}</span>
            <button onclick="increaseQuantity(${productId})">+</button>
        `;
    }
}

function showProductDetails(productId) {
    const product = products[currentCategory].find(p => p.id === productId);
    if (!product) {
        console.error('Product not found');
        return;
    }
    const modalContent = document.querySelector('#product-modal .modal-content');
    modalContent.querySelector('#modal-product-image').src = product.image;
    modalContent.querySelector('#modal-product-image').alt = product.name;
    modalContent.querySelector('#modal-product-name').textContent = product.name;
    modalContent.querySelector('#modal-product-description').textContent = product.description;
    modalContent.querySelector('#modal-product-price').textContent = `Цена: ${product.price} руб.`;
    modalContent.querySelector('#modal-quantity-control').innerHTML = renderQuantityControl(product.id);

    document.getElementById('product-modal').style.display = 'block';
}

function showCart() {
    const cartItems = document.getElementById('cart-items');
    const template = document.getElementById('cart-item-template');
    cartItems.innerHTML = '';
    let total = 0;

    Object.values(cart).forEach(item => {
        const itemElement = template.content.cloneNode(true);

        itemElement.querySelector('.cart-item-image').src = item.image;
        itemElement.querySelector('.cart-item-image').alt = item.name;
        itemElement.querySelector('.cart-item-name').textContent = item.name;
        itemElement.querySelector('.cart-item-price').textContent = `${item.price}`;
        itemElement.querySelector('.quantity').textContent = item.quantity;

        itemElement.querySelector('.minus').onclick = () => decreaseQuantity(item.id);
        itemElement.querySelector('.plus').onclick = () => increaseQuantity(item.id);
        itemElement.querySelector('.cart-item-remove').onclick = () => removeFromCart(item.id);

        cartItems.appendChild(itemElement);
        total += item.price * item.quantity;
    });

    document.getElementById('cart-total').textContent = `${total} сум`;
    document.getElementById('cart-modal').style.display = 'block';
}

function addToCart(productId) {
    const product = products[currentCategory].find(p => p.id === productId);
    if (!product) {
        console.error('Product not found');
        return;
    }
    if (cart[productId]) {
        cart[productId].quantity++;
    } else {
        cart[productId] = {...product, quantity: 1};
    }
    updateCartCount();
    renderProducts();
}

function removeFromCart(productId) {
    delete cart[productId];
    updateCartCount();
    showCart();
    renderProducts();
}

function increaseQuantity(productId) {
    cart[productId].quantity++;
    updateCartCount();
    showCart();
    renderProducts();
}

function decreaseQuantity(productId) {
    cart[productId].quantity--;
    if (cart[productId].quantity === 0) {
        removeFromCart(productId);
    } else {
        updateCartCount();
        showCart();
        renderProducts();
    }
}

function updateCartCount() {
    const count = Object.values(cart).reduce((sum, item) => sum + item.quantity, 0);
    document.getElementById('cart-count').textContent = count;
}

async function confirmOrder() {
    if (window.Telegram && window.Telegram.WebApp) {
        const orderData = {
            user_id: window.Telegram.WebApp.initDataUnsafe.user.id,
            items: Object.values(cart).map(item => ({
                id: item.id,
                name: item.name,
                price: item.price,
                quantity: item.quantity
            })),
            total_price: Object.values(cart).reduce((sum, item) => sum + item.price * item.quantity, 0)
        };

        try {
            // Отправка данных на бэкенд
            const response = await fetch('/api/create-order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(orderData)
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const result = await response.json();
            console.log('Order created:', result);

            // Отправка данных в Telegram WebApp
            window.Telegram.WebApp.sendData(JSON.stringify(orderData));

            // Закрытие WebApp
            window.Telegram.WebApp.close();
        } catch (error) {
            console.error('Error:', error);
            alert('Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте еще раз.');
        }
    } else {
        console.error('Telegram WebApp is not available');
        alert('Ошибка: Telegram WebApp недоступен');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    getProducts();

    document.getElementById('cart-button').addEventListener('click', showCart);
    document.getElementById('confirm-order').addEventListener('click', confirmOrder);
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            currentCategory = this.dataset.category;
            getProducts();
        });
    });

    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });
});

window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = "none";
    }
};
