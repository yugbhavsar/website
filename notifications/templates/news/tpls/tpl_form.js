function(modal){
    $('form.news-tpl-form', modal.body).submit(function(evt) {
	evt.preventDefault();
        var formdata = new FormData(this);
        $.ajax({
            url: this.action,
            data: formdata,
            processData: false,
            contentType: false,
            type: 'POST',
            dataType: 'text',
            success: function(response){
                modal.loadResponseText(response);
            }
        });
	return false;
    });
					       
    console.log('Success.');
}
