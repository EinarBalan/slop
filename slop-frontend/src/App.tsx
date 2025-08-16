import './App.css'
import likeIcon from './assets/like.svg';
// import commentIcon from './assets/comment.svg';
import forwardIcon from './assets/forward.svg';
import backIcon from './assets/back.svg';
import robotIcon from './assets/robot.svg';
import dislikeIcon from './assets/dislike.svg';
import { useState, useEffect } from 'react';

interface Post {
  title: string;
  post_id: string;
  over_18: string;
  subreddit: string;
  link_flair_text: string;
  self_text: string;
}

function Feed({ title, content, subreddit }: { title: string; content: string; subreddit: string }) {
  return (
    <div id="feed">
      <h1>{title}</h1>
      <p className="subreddit">r/{subreddit}</p>
      <p>{content}</p>
    </div>
  )
}

function InteractionButton({ icon, onClick }: { icon: string, onClick: () => void }) {
  return (
    <button className="interaction-button" onClick={onClick}>
      <img src={icon} alt="icon" />
    </button>
  )
}

function Controls({ nextPost, prevPost, currentPost }: { nextPost: () => void, prevPost: () => void, currentPost: Post }) {
  const handleLike = async () => {
    try {
      const response = await fetch('http://localhost:3000/interactions/like', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentPost)
      });
      const data = await response.json();
      console.log('Like response:', data);
    } catch (error) {
      console.error('Error liking post:', error);
    }
  };

  const handleDislike = async () => {
    try {
      const response = await fetch('http://localhost:3000/interactions/dislike', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentPost)
      });
      const data = await response.json();
      console.log('Dislike response:', data);
    } catch (error) {
      console.error('Error disliking post:', error);
    }
  };

  const handleJudgeAI = async () => {
    try {
      const response = await fetch('http://localhost:3000/interactions/judgeAI', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          post: currentPost,
          isAI: currentPost.link_flair_text === 'AI'
        })
      });
      const data = await response.json();
      console.log('AI judgment response:', data);
    } catch (error) {
      console.error('Error judging AI post:', error);
    }
  };

  return (
    <div id="controls">
      <InteractionButton icon={likeIcon} onClick={handleLike} />
      <InteractionButton icon={robotIcon} onClick={handleJudgeAI} />
      <InteractionButton icon={dislikeIcon} onClick={handleDislike} />
      <InteractionButton icon={backIcon} onClick={prevPost} />
      <InteractionButton icon={forwardIcon} onClick={nextPost} />
    </div>
  )
}

function App() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [currentPostIndex, setCurrentPostIndex] = useState(0);

  const nextPost = () => {
    fetch('http://localhost:3000/interactions/next', { // for stats purposes
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(posts[currentPostIndex])
    });

    if (currentPostIndex >= posts.length - 5) {
      console.log(posts);
      // Get next batch of real posts
      fetch('http://localhost:3000/feed')
        .then(response => response.json())
        .then(data => {
          setPosts([...posts, ...data.posts]);
        });
    } else {
      setCurrentPostIndex(currentPostIndex + 1);
    }
  }

  const prevPost = () => {
    if (currentPostIndex > 0) {
      setCurrentPostIndex(currentPostIndex - 1);
    }
  }

  // retrieve real posts and initial AI posts
  useEffect(() => {
    fetch('http://localhost:3000/feed')
      .then(response => response.json())
      .then(data => {
        setPosts(data.posts);
      });
  }, []);

  return (
    <div id="app">
      <Feed 
        title={posts[currentPostIndex]?.title} 
        content={posts[currentPostIndex]?.self_text}
        subreddit={posts[currentPostIndex]?.subreddit}
      />
      <Controls 
        nextPost={nextPost} 
        prevPost={prevPost} 
        currentPost={posts[currentPostIndex]}
      />
    </div>
  )
}

export default App
