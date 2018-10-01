
$( document ).ready( 
    function () {
	var right = $('.row.nice-padding .right');
	var btns = [
	    '<a class="button template-button" href="/rubionadmin/news/templates/emergency_power_test/">Vorlage: Notstromprobe</a>',
	    '<a class="button template-button" href="/rubionadmin/news/templates/air_condition_test/">Vorlage: Lüftungswartung</a>',
	    '<a class="button template-button" href="/rubionadmin/news/templates/alarm_test/">Vorlage: Hausalarmprüfung</a>'
	];
	right.html(btns.join(' '));
    }
);

$( document ).ready(function(){
    console.log('In ready...');
    $('.template-button').click(function(evt){
	evt.preventDefault();
	ModalWorkflow({
	    url : $(this).attr('href'),
	    responses : {
		setvalues : function(data){
		    console.log('Setting values');
		    for (key in data) {
			$('#id_'+key).val(data[key]);
			if ($('#id_'+key).prev().hasClass('richtext')){
			    $('#id_'+key).prev().html(data[key]);
			}
			$('#id_'+key+'[type=checkbox]').prop("checked", data[key]);
		    }
		}
	    }
	});
    });
})
