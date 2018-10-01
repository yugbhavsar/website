function rubion_ajaxify( elements, success_fnc, data_fnc ){
  var csrftoken = $("[name=csrfmiddlewaretoken]").val();
  $(elements).each( 
    function(){
      var btn = $(this);
      btn.click(
        function( ev ){
          ev.preventDefault();
          var dataObj = {}
          if (data_fnc){
            dataObj['data'] = data_fnc(btn);
          }
          $.ajax($.extend(dataObj, {
            'beforeSend': function(xhr, settings){
              if (!this.crossDomain){
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
              }
            },
            'url' : $(this).attr('href'),
            'method' : 'POST',
            'success' : function(data, status, jqXHR){success_fnc(data, status, jqXHR, btn);}
          }));
        }
      );
    }
  );
}


$(document).ready(function(){
    rubion_ajaxify(
	$('.ajax-button'), 
	function(data, status, jqXHR, btn)
	{
	    if (data['lang'] === 'de'){
		$('.time', btn).html('erneuert');
	    } 
	    else {
		$('.time', btn).html('renewed');
	    }
	    btn.removeClass('no').addClass('yes');
	}
    );

});
