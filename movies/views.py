from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Report
from django.contrib.auth.decorators import login_required

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
        
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html',
                  {'template_data': template_data})

#if the user is auth -> grab the ids of the reviews that they reported and
#  then filter the reviews list to not show them to that specific user
def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)
    if request.user.is_authenticated:
        reported_ids_reviews = Report.objects.filter(user=request.user).values_list('review_id', flat = True)
        reviews = reviews.exclude(id__in = reported_ids_reviews) 
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    return render(request, 'movies/show.html', {'template_data': template_data})

@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
    
@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html',
            {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)


#report function:
# creates a review variable that gets the review object or 404 if not found
#if 'POST' and comment for report isn't empty then create a new report object in database
# get the report comment, review, user. then redirect back to the move
#else: prepares template to show report.html and sending the review field to it
@login_required
def report(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST' and request.POST['comment'] != '':
        reports = Report()
        reports.report = request.POST['comment']
        reports.review = review
        reports.user = request.user
        reports.movie = review.movie
        reports.save()
        return redirect('movies.show', id=id)
    
    else:
        template_data = {}
        template_data['review'] = review
        return render(request, 'movies/report.html', {'template_data': template_data})