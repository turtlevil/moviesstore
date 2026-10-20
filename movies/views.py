from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Report
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
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
#grab the users review for that specific movie
def show(request, id):
    movie = Movie.objects.get(id=id)
    movie_rating = Review.objects.filter(movie = movie).aggregate(Avg('rating'))['rating__avg']
    reviews = Review.objects.filter(movie=movie)
    user_review = None
    if request.user.is_authenticated:
        reported_ids_reviews = Report.objects.filter(user=request.user).values_list('review_id', flat = True)
        reviews = reviews.exclude(id__in = reported_ids_reviews) 
        user_review = Review.objects.filter(movie = movie, user = request.user).first()
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['movie_rating'] = movie_rating
    template_data['reviews'] = reviews
    template_data['user_review'] = user_review

    return render(request, 'movies/show.html', {'template_data': template_data})


#get movie, make sure user doesn't have review for it
#check there's a rating and there isn't  review already for this user
@login_required
def create_review(request, id):
    movie = Movie.objects.get(id=id)
    review_exists = Review.objects.filter(movie = movie, user = request.user).exists()
    if request.method == 'POST' and request.POST.get('rating') in ['1', '2', '3', '4', '5'] and not review_exists:
        movie = Movie.objects.get(id=id)
        review = Review()
        review.rating = int(request.POST.get('rating'))
        review.comment = request.POST.get('comment', '')
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
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST.get('rating') in ['1', '2', '3', '4', '5']:
        review = Review.objects.get(id=review_id)
        review.rating = int(request.POST.get('rating'))
        review.comment = request.POST.get('comment', '')
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

@staff_member_required
def top_commenters(request):
    commenters = (
        Review.objects.exclude(comment__regex=r'^\s*$')
        .values('user_id', 'user__username')
        .annotate(comments_posted=Count('id'))
        .order_by('-comments_posted', 'user_id')
    )
    template_data = {}
    template_data['title'] = 'Top Commenters'
    template_data['commenters'] = commenters
    template_data['top_commenters'] = commenters.first()
    return render(request, 'movies/top_commenters.html',
        {'template_data': template_data})

@staff_member_required
def top_movies(request):
    top_bought = (
        Movie.objects.annotate(times_bought=Sum('item__quantity')).filter(times_bought__gt=0).order_by('-times_bought', 'name').first()
    )
    top_reviewed = (
        Movie.objects.annotate(times_reviewed=Count('review')).filter(times_reviewed__gt=0).order_by('-times_reviewed', 'name').first()
    )

    template_data = {}
    template_data['title'] = 'Top Movies'
    template_data['top_bought'] = top_bought
    template_data['top_reviewed'] = top_reviewed
    return render(request, 'movies/top_movies.html', {'template_data' : template_data})
