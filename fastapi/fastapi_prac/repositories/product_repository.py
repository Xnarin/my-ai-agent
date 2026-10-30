from schemas.product import Product, ProductRequest


class ProductRepository:
    def __init__(self):
        self.products = []
        self.product_id = 0

    def save(self, new_product: Product):
        self.product_id += 1
        new_product.id = self.product_id
        self.products.append(new_product)
        return new_product

    def find_all(self, keyword: str | None = None):
        if keyword:
            return [product for product in self.products if keyword in product.name]
        return self.products

    def find_by_id(self, product_id: int):
        for product in self.products:
            if product.id == product_id:
                return product
        return None

    def update(self, product_id: int, data: ProductRequest):
        for product in self.products:
            if product.id == product_id:
                product.name = data.name
                product.price = data.price
                product.discount_price = data.discount_price
                product.stock = data.stock
                product.category = data.category
                return product
        return None


product_repository = ProductRepository()
