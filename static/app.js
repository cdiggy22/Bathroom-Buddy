// app for bathroom buddy 


$( "a" ).hover(
  function() {
      $(this).find("span").stop().animate({
      width:"100%",
      opacity:".5",
    }, 400, function () {
    })
  }, function() {
      $(this).find("span").stop().animate({
      width:"0%",
      opacity:"0",
    }, 400, function () {
    })
  }
);