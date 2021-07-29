Array.prototype.last = (array)=>{
    if (array.length == 0) return none;
    return array[array.length-1];
}
toastr.options = {
    "closeButton": true,
    "newestOnTop": false,
    "progressBar": true,
    "positionClass": "toast-bottom-left",
    "preventDuplicates": false,
    "onclick": null,
    "showDuration": "300",
    "hideDuration": "1000",
    "timeOut": "5000",
    "extendedTimeOut": "1000",
    "showEasing": "swing",
    "hideEasing": "linear",
    "showMethod": "fadeIn",
    "hideMethod": "fadeOut"
}

$(function(ready){
    // Register
    $('input[name="is_teacher"]').change(()=>{
        const text = $('input[name="is_teacher"]').prop('checked')? "شماره استادی" : "شماره دانشجویی";        
        $("label[for='identifier']").text(text);
    });
    $("table").parent().css({"overflow-x":"auto", "position": "relative", "z-index":"0"});
    
    $(".sidebar a").off().click(e=>{        
        const that = $(e.target);
        $(that).parent().siblings('li').find('a').removeClass('active');
        $(that).addClass('active');
        $("article").addClass("d-none");
        const target = $(that).data("target");
        $("#"+target).removeClass('d-none');
    });
    if (document.location.hash){
        $(`.sidebar a[data-target=${document.location.hash.slice(1)}]`).click();
    }

    if (document.location.href.indexOf("edit_exam")){
        append_question_to_page($("<i class='d-none'>"), $("body"));
    }
    $("[data-target='#exampleModal']").click((e)=>{
        var modal = $('#exampleModal');
        modal.modal("show");
        var button = $(e.target);
        var type = button.data('whatever');
        let label_name = modal.find('[for="recipient-name"]');
        let label_code = modal.find('[for="message-text"]');
        let inp_name = modal.find('input#name');
        let inp_code = modal.find('input#code');
        inp_name.val("");
        inp_code.val("");
        let url = "", type_text="", name_field = "", code_field="";
        if (type == "teacher"){
            type_text="استاد";
            url = "/new_teacher";
            name_field = "نام استاد";
            code_field = "کد استادی";
        }else if (type == "student"){
            type_text="دانشجو";
            url = "/new_student";
            name_field = "نام دانشحو";
            code_field = "کد دانشجویی";
        }else{
            type_text="درس";
            url = "/new_course";
            name_field = "نام درس";
            code_field = "تعداد واحد";
        }
        
        label_name.text(name_field);
        label_code.text(code_field);
        modal.find('.modal-title').text('ایجاد ' + type_text);
        modal.find("button.close").off().click(()=>{
            modal.modal('hide');
        });
        modal.find('button.create').off().click((e)=>{
            let data = {
                name: inp_name.val(), 
                code: inp_code.val()
            }
            fetch(url, {
                method: 'POST', 
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
            .then(response => response.json())
            .then(data => {
                if(data.result == "success"){
                    modal.modal('hide');
                    document.location.reload();
                    toastr.success("با موفقیت ایجاد شد.")
                }else{
                    toastr.error(data.cause)
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
        });
    });

    $(".add_new_course").off().click((e)=>{
        $(".add_to_lessons").removeClass('d-none');
    }); 
    
    $(".add_to_lessons .submit").off().click((e)=>{
        let selected = $(".add_to_lessons select :selected").val();
        if (!selected){
            $(".add_to_lessons .select").focus();
            return;
        }
        fetch(`/add_course_to_user/${selected}`).then((response)=>{
            response.json().then((data)=>{
                if (data.result == 'success'){
                    toastr.success("با موفقیت ثبت شد");
                    setTimeout(() => {
                        document.location.reload();
                    }, 1000);
                }else{
                    toastr.error(data.cause);
                }
            });
        });
    }); 
    let edit_from = $("#edit_exam .exam_form input#datetime").persianDatepicker({
        format:"L HH:mm",
        initialValue: ($("input#datetime").attr("unix") && +$("input#datetime").attr("unix")*1000) || false ,
        autoClose: false,
        toolbox: false,
        toolbox:{
            submitButton: {
                enabled: true,
                onSubmit: ()=>{
                    let unix = edit_from.getState().selected.unixDate;
                    $("#edit_exam_date_unix").val(unix); 
                    edit_from.hide();
                }
            },
            calendarSwitch: {
                enabled: false
            }
        },
        navigator:{
            scroll:{
                enabled: false
            }
        },
        minDate: new persianDate(),
        timePicker: {
            enabled: true,
            meridiem: {
                enabled: true
            },
            second: {
                enabled: false
            }
        },
    });
    let new_from = $("#new_exam .exam_form input#datetime").persianDatepicker({
        format:"L HH:mm",
        initialValue:false,
        autoClose:false,
        toolbox: false,
        toolbox:{
            submitButton: {
                enabled: true,
                onSubmit: ()=>{
                    let unix = new_from.getState().selected.unixDate;
                    $("#create_exam_date_unix").val(unix); 
                    new_from.hide();
                }
            },
            calendarSwitch: {
                enabled: false
            }
        },
        navigator:{
            scroll:{
                enabled: false
            }
        },
        minDate: new persianDate(),
        timePicker: {
            enabled: true,
            meridiem: {
                enabled: true
            },
            second: {
                enabled: false
            }
        },
    });
   
    $('form#create_new_exam').off().submit((e)=>{
        e.preventDefault();
       
        var url = "/create_new_exam";
        $.post({
            url: url,
            data: $('form#create_new_exam').serialize(), 
        }).done((data)=>{
            if (data.result == "success"){
                toastr.success("با موفقیت ثبت شد.");
                $(".add_new_question_placeholder").removeClass('d-none');
                const exam_id = Number(data.exam_id);
                $(".add_new_question_placeholder").off().click((e)=>{
                    const question_number = $("#new_exam .question_form").length+1;
                    fetch(`/get_question_template/${question_number}/exam_${exam_id}`).then((response)=>{
                        response.json().then((data)=>{
                            append_question_to_page(data.body, $("article#new_exam .add_new_question_placeholder"));
                        });
                    });
                });
            }else{
                toastr.error(data.cause);
            }
        });
    });
    // Edit exam save details form
    $('form#edit_exam_form').off().submit((e)=>{
        e.preventDefault();
        const form = $('form#edit_exam_form');
        const _exam_id = form.data("exam_id");
        var url = `/update_exam/${_exam_id}`; 
        $.post({
            url: url,
            data: form.serialize(), 
        }).done((data)=>{
            if (data.result == "success"){
                toastr.success("با موفقیت ثبت شد.");
            }else{
                toastr.error(data.cause);
            }
        });
    });
    // EDIT FORM ADD QUESTION
    
    // Edit - Get exam info
    $("button#edit_exam").off().click(()=>{
        const exam_id = $("select.select_exam_for_edit :selected").val();
        document.location.href = '/teacher/edit_exam/'+exam_id; 
        return;
    });
   
    $("#edit_placeholder").off().click((e)=>{
        const edit_placeholder = $("#edit_placeholder");
        const question_number = $("#edit_exam .question_form").length+1;
        const exam_id = edit_placeholder.data("exam_id")
        fetch(`/get_question_template/${question_number}/exam_${exam_id}`).then((response)=>{
            response.json().then((data)=>{
                append_question_to_page(data.body, edit_placeholder);
            });
        });
    });
    // Init countdowns
    const counters = $('.countdown_counter');
    $(counters).each((i, counter)=>{
        const deadline = new Date($(counter).data('unix') *1000);
        initializeClock(counter, deadline);
    }) ;
    $(".delete_exam").off().click((e)=>{
        const form = $(e.target).parents("form");
        const id = +form.data('exam_id');
        fetch("/exam/delete/"+id)
        .then(response => response.json().then(data=>{
            if (data.result == "success"){
                toastr.success("حذف شد")
                setTimeout(() => {
                    document.location.reload();
                }, 1000);
            }else{
                toastr.error(data.cause);
            }
        }));
    });

    if ( $("#exam_timer").length ){
        const timer = $("#exam_timer");
        const duration = +timer.data('duration') || 1;
        
        const diff =  new Date(+timer.data("unix")*1000 +  duration*60*1000) - new Date();
        timer.countdown({
            diff: diff
        },()=>{
            fetch("/complete_exam/"+$("input#exam_id").val())
            .then(r=>r.json())
            .then(data=>{
                if (data.result == 'success'){
                    document.location.href = "/exam_result/"+ $("input#exam_id").val();
                    window.addEventListener('popstate', function (event) {
                        history.pushState(null, document.title, location.href);
                      });
                }
            });
        });
    }
    $(".delete_question").off().click((e)=>{
        const form = $(e.target).parents("form");
        const id = +form.data('question_id');
        if (!id) {form.parent().detach();return;}
        fetch("/question/delete/"+id)
        .then(response => response.json().then(data=>{
            form.parent().detach();
            toastr.success("با موفقیت حذف شد.")
        }));
    });
    $("button.submit_answer").off().click(e=>{
        const btn = $("button.submit_answer");
        const qid = btn.data('qid');
        const submit = +$("[name=answer]:checked").val();
        fetch(`/submit_answer/${qid}/${submit}`)
        .then(response => response.json())
        .then(result => {
            if (result.result == 'success'){
                $('.text-success').removeClass('d-none');
                $('li.current').addClass('active');
                toastr[result.result](result.msg);
            }else{
                document.location.href = result.redirect;
            }

        });
    });
    $(".end_exam").off().click(e=>{
        $("#end_exam_modal").modal("show");
    });
    $("#end_exam_modal").on('shown.bs.modal', function(){
        $(this).find("button.btn-primary").off().click(e=>{
            fetch("/complete_exam/"+$("input#exam_id").val())
            .then(r=>r.json())
            .then(data=>{
                if (data.result == 'success'){
                    document.location.href = "/exam_result/"+ $("input#exam_id").val();
                    window.addEventListener('popstate', function (event) {
                        history.pushState(null, document.title, location.href);
                    });
                }
            });
        });
    });
    $("body").click((e)=>{
        if ($(e.target).parents('.sidebar').length == 0 && $(".sidebar.open").length >0)
            $('.toggle_sidebar').click();
    });
});
function changeBackground(img){
    let preview_div = $(img).siblings("div.image_preview");
    var file = img.files[0];
    var imagefile = file.type;
    var match= ["image/jpeg","image/png","image/jpg"];
          if(!((imagefile==match[0]) || (imagefile==match[1]) || (imagefile==match[2]))){
                alert("Invalid File Extension");
          }else{
                var reader = new FileReader();
                reader.onload = imageIsLoaded;
                reader.readAsDataURL(img.files[0]);
          }
    function imageIsLoaded(e) {
        preview_div.find(".placeholder").addClass('d-none');
        preview_div.find(".help_text").removeClass('d-none');
        preview_div.css({ 'background-image': "url(" + e.target.result + ")" });
    }     
}
function getTimeRemaining(endtime) {
    const total = Date.parse(endtime) - Date.parse(new Date());
    const seconds = Math.floor((total / 1000) % 60);
    const minutes = Math.floor((total / 1000 / 60) % 60);
    const hours = Math.floor((total / (1000 * 60 * 60)) % 24);
    const days = Math.floor(total / (1000 * 60 * 60 * 24));
    
    return {
      total,
      days,
      hours,
      minutes,
      seconds
    };
}
  
    function initializeClock(parent_td, endtime) {
        const clock = $("<div class='clock'><div class='seconds'></div>:<div class='minutes'></div>:<div class='hours'></div>:<div class='days'></div></div>");
        $(parent_td).append(clock);
        const daysSpan = clock.find('.days');
        const hoursSpan = clock.find('.hours');
        const minutesSpan = clock.find('.minutes');
        const secondsSpan = clock.find('.seconds');
    
        function updateClock() {
            const t = getTimeRemaining(endtime);
        
            $(daysSpan).text(t.days);
            $(hoursSpan).text(('0' + t.hours).slice(-2));
            $(minutesSpan).text(('0' + t.minutes).slice(-2));
            $(secondsSpan).text(('0' + t.seconds).slice(-2));
        
            if (t.total <= 0) {
                if(timeinterval)
                    clearInterval(timeinterval);
                clock.detach();
                $(parent_td).find(".enter").removeClass('hidden');
            }
        }
  
        const timeinterval = setInterval(updateClock, 1000);
        
    }

function toggle_sidebar(e) {
    e.stopPropagation();
    $(".sidebar").toggleClass("open");
    $(e.target).toggleClass("bi-x")
}
function save_question(e) {
    e.preventDefault();
    const form = $(e.target);
    const data = form.serialize();
    const qid = form.data("question_id");
    let url =  +qid? form.prop("action") + "/"+qid : form.prop("action");
    const formdata = new FormData(form[0]);
    fetch(url, {
        method:"POST",
        body: formdata
    }).then((response)=>{
        response.json().then((data)=>{
            if (data.result == "success")
                toastr.success("با موفقیت ثبت شد");
            else
                toastr.error(data.cause);
        });
    });
}
function append_question_to_page(elem, before, parent){
    before.before(elem);
    $("form.save_question_form").off().submit(save_question);
    // $("button.save_question").off().click(e=>{$(e.target).parents('form').submit();});
    
    $('div.image_preview').off().click((e)=>{
        $(e.target).siblings('input').click();
    });
    $("input.image_input").off().change(function(){
        var length=this.files.length;
        if(!length){
            return false;
        }
        changeBackground(this);
    });
}

