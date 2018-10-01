function createRejectionModal() {
    var btns = $('.reject-button');
    btns.each( 
	function( ){
	    var form = $(this).parent();
	    form.submit(
		function( evt ) {

		    //Prevent sending the form
		    evt.preventDefault();

		    // get the id 
		    var url_parts = form.attr('action').split('/');
		    var r_url = window.rubionadmin.reject_form_url + url_parts[3] + '/'
		    ModalWorkflow({
			url : r_url,
			responses : {

			}
		    }
		    );
		    
		    return false;
		}
	    );
	}
    );
}

$( document ).ready(createRejectionModal);

