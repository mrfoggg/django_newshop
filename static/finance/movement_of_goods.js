$(document).ready(()=>{


});

function fill_table(response) {
    console.log('RESP - ', response.data);
    console.log('reportTable - ', $('#reportTable'));
    let stockRow;
    let productRow;
    for (let stockData of response.data.stocks) {
        console.log('stockData ', stockData)
        stockRow = `<tr>
                    <td class="stock">${stockData.name}</td>
                    <td class="stock_total">${stockData.before}</td>
                    <td class="stock_total">${stockData.arrived}</td>
                    <td class="stock_total">${stockData.sent}</td>
                    <td class="stock_total">${stockData.after}</td>
               </tr>`
        $('#reportTable').append(stockRow);
        for (let productData of stockData.products){
            productRow = `<tr>
                        <td class="product">${productData.name}</td>
                        <td class="product_total">${productData.before}</td>
                        <td class="product_total">${productData.arrived}</td>
                        <td class="product_total">${productData.sent}</td>
                        <td class="product_total">${productData.after}</td>
                   </tr>`
            $('#reportTable').append(productRow);
            for (let documentRow of productData.documents){
                documentRow = `<tr>
                            <td class="document">${documentRow.name}</td>
                            <td>${documentRow.before}</td>
                            <td>${documentRow.arrived}</td>
                            <td>${documentRow.sent}</td>
                            <td>${documentRow.after}</td>
                       </tr>`
                $('#reportTable').append(documentRow);
            }
        }



        console.log('LAST ROW - ', $('#reportTable tr').last());

    }
}