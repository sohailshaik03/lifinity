from Retailsights.repositories.orm_adapters import shops_adapter, products_adapter

# create a shop and a product as smoke test
shop = shops_adapter.create_shop('Smoke Shop', address='{}', city='Testville', country='Testland')
print('Created shop id', shop.id)
prod = products_adapter.create_product(shop.id, 'Smoke Product', sku='SMK1', default_cost=2.5)
print('Created product id', prod.id)
prods = products_adapter.get_products_by_shop(shop.id)
print('Products for shop:', [(p.id,p.name) for p in prods])
