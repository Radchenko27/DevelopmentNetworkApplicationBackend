from django.shortcuts import render

# Create your views here.
fixtures = {




}



def drivers_list(request):
    # features = FeatureRequest.objects.all()
    return render(request, 'drivers_list.html')




def driver_detail(request):
    # bug = get_object_or_404(BugReport, id=bug_id)
    return render(request, 'product_detail.html')