def get_margin(purchase_price, sale_price):
    return sale_price - purchase_price if purchase_price and sale_price else '-'


def get_margin_percent(margin, purchase_price):
    return '-' if margin == '-' else f'{margin.amount / purchase_price.amount * 100:.2f} %'


def get_profitability(margin, sale_price):
    return '-' if margin == '-' else f'{margin.amount / sale_price.amount * 100:.2f} %'
