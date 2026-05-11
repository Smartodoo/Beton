$(document).ready(function () {

    if(localStorage.getItem("is_night_mode") && localStorage.getItem("is_night_mode") == 't'){
        $('.o_web_client').addClass('sh_night_mode');
    }else{
        $('.o_web_client').removeClass('sh_night_mode');
    }
    
    $(document).on("click", "#action_preview_theme_style_1", function (ev) {
        
        var img_src = $("input[name=img_src]").val();
           $("#js_id_theme_preview_image").attr('src', 'sh_back_theme_config/static/src/img/preview/theme/theme_style_img.png');
 
           });


    $(document).on("click", ".sh_close_notification", function () {
        $("#object").css("display", "none");
        $("#object1").css("display", "none");
    });
   
    $('.o_web_client').on('click', ".o_action_manager", function (ev) {

         //$('.sh_search_results').css("display","none");
         $('.todo_layout').removeClass("sh_theme_model");
         if ($('.sh_calc_util').hasClass('active')) {
             $('.open_calc').click();
         }
         //	$('.o_action_manager').css("margin-right","0px")
         $('.sh_search_results').css("display", "none");

         if($('.sh_user_language_list_cls').css("display") != 'none'){
            $('.sh_user_language_list_cls').css("display","none")
         }
         if($('.sh_wqm_quick_menu_submenu_list_cls').css("display") != 'none'){
            $('.sh_wqm_quick_menu_submenu_list_cls').css("display","none")
         }

         if($('.sh_calc_util').hasClass("active")){
            $('.sh_calc_util').removeClass("active")
         }
         $('.backmate_theme_layout').removeClass("sh_theme_model");
         
    });
    
    $(document).on("click", ".sh_close_notification", function () {
        $("#object").css("display", "none");
        $("#object1").css("display", "none");
    });

    $('body').keydown(function (e) {
        
        if ($("body").hasClass("sh_sidebar_background_enterprise")) {
            $(".sh_search_container").css("display", "block");
            $(".usermenu_search_input").focus();
            $(".sh_entmate_theme_appmenu_div").css("opacity", "0")
            /*if(!$("body").hasClass("sh_detect_first_keydown")){
                $(".usermenu_search_input").keydown()
            }*/
         
        }
    });

    
    if ("serviceWorker" in navigator) {
            navigator.serviceWorker.register("/firebase-messaging-sw.js")
                .catch((error) => {
                    console.error("Service worker registration failed, error:", error);
                });
        }




});