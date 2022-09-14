#!/usr/bin/env python
import os
import random
from flask import Flask, jsonify

app = Flask(__name__)

quotes = [{
    "text":
    "The best thing about giving of ourselves is that what we get is always better than what we give. The reaction is greater than the action.",
    "author": "Orison Swett Marden",
}, {
    "text":
    "The best government is that which teaches us to govern ourselves.",
    "author": "Johann Wolfgang von Goethe",
}, {
    "text":
    "The scientific theory I like best is that the rings of Saturn are composed entirely of lost airline luggage.",
    "author": "Mark Russell",
}, {
    "text":
    "Falling in love is the best way to kill your heart because then it's not yours anymore. It's laid in a coffin, waiting to be cremated.",
    "author": "Ville Valo",
}, {
    "text": "You'll live. Only the best get killed.",
    "author": "Charles de Gaulle",
}, {
    "text":
    "The best way to get a bad law repealed is to enforce it strictly.",
    "author": "Abraham Lincoln",
}, {
    "text":
    "Look at the sky. We are not alone. The whole universe is friendly to us and conspires only to give the best to those who dream and work.",
    "author": "Abdul Kalam",
}, {
    "text": "The only way to get the best of an argument is to avoid it.",
    "author": "Dale Carnegie",
}, {
    "text":
    "You're not going to say anything about me that I'm not going to say about myself. There's so many things that I think about myself if someone really wanted to get at me, they could say this and this and this. So I'm going to say it before they can. It's the best policy for me.",
    "author": "Eminem",
}, {
    "text": "The best way out of a difficulty is through it.",
    "author": "Will Rogers",
}, {
    "text":
    "A man is relieved and gay when he has put his heart into his work and done his best but what he has said or done otherwise shall give him no peace.",
    "author": "Ralph Waldo Emerson",
}, {
    "text": "The best way out is always through.",
    "author": "Robert Frost",
}, {
    "text":
    "It is not best that we should all think alike it is a difference of opinion that makes horse races.",
    "author": "Mark Twain",
}, {
    "text": "Do the best you can, and don't take life too serious.",
    "author": "Will Rogers",
}, {
    "text":
    "My dad was my best friend and greatest role model. He was an amazing dad, coach, mentor, soldier, husband and friend.",
    "author": "Tiger Woods",
}, {
    "text": "Having lots of siblings is like having built-in best friends.",
    "author": "Kim Kardashian",
}, {
    "text": "The best way out is always through.",
    "author": "Robert Frost",
}, {
    "text":
    "Nothing goes by luck in composition. It allows of no tricks. The best you can write will be the best you are.",
    "author": "Henry David Thoreau",
}, {
    "text": "Sleep is the best meditation.",
    "author": "Dalai Lama",
}, {
    "text":
    "The principle of all successful effort is to try to do not what is absolutely the best, but what is easily within our power, and suited for our temperament and condition.",
    "author": "John Ruskin",
}, {
    "text":
    "Don't let the fear of the time it will take to accomplish something stand in the way of your doing it. The time will pass anyway we might just as well put that passing time to the best possible use.",
    "author": "Earl Nightingale",
}, {
    "text": "The best way to predict the future is to invent it.",
    "author": "Alan Kay",
}, {
    "text":
    "The best and safest thing is to keep a balance in your life, acknowledge the great powers around us and in us. If you can do that, and live that way, you are really a wise man.",
    "author": "Euripides",
}, {
    "text":
    "In the practical art of war, the best thing of all is to take the enemy's country whole and intact to shatter and destroy it is not so good.",
    "author": "Sun Tzu",
}, {
    "text":
    "A failure is not always a mistake, it may simply be the best one can do under the circumstances. The real mistake is to stop trying.",
    "author": "B. F. Skinner",
}, {
    "text":
    "An educated person is one who has learned that information almost always turns out to be at best incomplete and very often false, misleading, fictitious, mendacious - just dead wrong.",
    "author": "Russell Baker",
}, {
    "text": "I have the simplest tastes. I am always satisfied with the best.",
    "author": "Oscar Wilde",
}, {
    "text":
    "We all like to forgive, and love best not those who offend us least, nor who have done most for us, but those who make it most easy for us to forgive them.",
    "author": "Samuel Butler",
}, {
    "text":
    "Good humor is a tonic for mind and body. It is the best antidote for anxiety and depression. It is a business asset. It attracts and keeps friends. It lightens human burdens. It is the direct route to serenity and contentment.",
    "author": "Grenville Kleiser",
}, {
    "text":
    "The best way to obtain truth and wisdom is not to ask from books, but to go to God in prayer, and obtain divine teaching.",
    "author": "Joseph Smith, Jr.",
}, {
    "text":
    "Health is the greatest gift, contentment the greatest wealth, faithfulness the best relationship.",
    "author": "Buddha",
}, {
    "text": "He who laughs best today, will also laughs last.",
    "author": "Friedrich Nietzsche",
}, {
    "text": "There are some things you learn best in calm, and some in storm.",
    "author": "Willa Cather",
}, {
    "text":
    "Now I see the secret of making the best person: it is to grow in the open air and to eat and sleep with the earth.",
    "author": "Walt Whitman",
}, {
    "text": "Friends are the best to turn to when you're having a rough day.",
    "author": "Justin Bieber",
}, {
    "text":
    "The best work is not what is most difficult for you it is what you do best.",
    "author": "Jean-Paul Sartre",
}, {
    "text":
    "When a place gets crowded enough to require ID's, social collapse is not far away. It is time to go elsewhere. The best thing about space travel is that it made it possible to go elsewhere.",
    "author": "Robert A. Heinlein",
}, {
    "text":
    "The best way to navigate through life is to give up all of our controls.",
    "author": "Gerald Jampolsky",
}, {
    "text": "Youth is the best time to be rich, and the best time to be poor.",
    "author": "Euripides",
}, {
    "text": "We do not look in our great cities for our best morality.",
    "author": "Jane Austen",
}, {
    "text":
    "Every year of my life I grow more convinced that it is wisest and best to fix our attention on the beautiful and the good, and dwell as little as possible on the evil and the false.",
    "author": "Richard Cecil",
}, {
    "text": "The things we know best are the things we haven't been taught.",
    "author": "Luc de Clapiers",
}, {
    "text":
    "No man really knows about other human beings. The best he can do is to suppose that they are like himself.",
    "author": "John Steinbeck",
}, {
    "text":
    "In the misfortunes of our best friends we always find something not altogether displeasing to us.",
    "author": "Francois de La Rochefoucauld",
}, {
    "text":
    "You and I are stuck with the necessity of taking the worst of two evils or none at all. So-I'm taking the immature Democrat as the best of the two. Nixon is impossible.",
    "author": "Harry S. Truman",
}, {
    "text":
    "There is one rule for the industrialist and that is: Make the best quality of goods possible at the lowest cost possible, paying the highest wages possible.",
    "author": "Henry Ford",
}, {
    "text":
    "My best friend is the man who in wishing me well wishes it for my sake.",
    "author": "Aristotle",
}, {
    "text":
    "Cynical realism is the intelligent man's best excuse for doing nothing in an intolerable situation.",
    "author": "Aldous Huxley",
}, {
    "text": "The best way out is always through.",
    "author": "Robert Frost",
}, {
    "text":
    "I've run the Boston Marathon 6 times before. I think the best aspects of the marathon are the beautiful changes of the scenery along the route and the warmth of the people's support. I feel happier every time I enter this marathon.",
    "author": "Haruki Murakami",
}]


@app.route("/")
def index():
    """Simple REST API to return a random quote."""
    return jsonify(random.choice(quotes))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
