from django.shortcuts import render

# Create your views here.
fixtures = {




}



def drivers_list(request):
    # features = FeatureRequest.objects.all()
    return render(request, 'drivers/drivers_list.html')




def driver_detail(request):
    # bug = get_object_or_404(BugReport, id=bug_id)
    return render(request, 'drivers/driver_detail.html')


def request_detail(request):
    # bug = get_object_or_404(BugReport, id=bug_id)
    return render(request, 'drivers/request_detail.html')