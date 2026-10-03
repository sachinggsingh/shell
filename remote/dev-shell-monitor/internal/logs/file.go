package logs

import (
	"bufio"
	"context"
	"io"
	"os"
	"time"

	"dev-shell-monitor/internal/config"
	"dev-shell-monitor/internal/model"
)

func ReadFile(ctx context.Context, source config.FileSource, publish func(model.Log)) error {
	if source.Path == "" {
		return nil
	}
	var offset int64
	var inode uint64
	initialized := false
	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}
		info, err := os.Stat(source.Path)
		if err != nil {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(500 * time.Millisecond):
				continue
			}
		}
		currentInode := fileInode(info)
		file, err := os.Open(source.Path)
		if err != nil {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(500 * time.Millisecond):
				continue
			}
		}
		if !initialized {
			offset, _ = file.Seek(0, io.SeekEnd)
			inode = currentInode
			initialized = true
		} else if currentInode != inode || info.Size() < offset {
			offset = 0
			inode = currentInode
		}
		if _, err := file.Seek(offset, io.SeekStart); err != nil {
			_ = file.Close()
			return err
		}
		reader := bufio.NewReader(file)
		for {
			select {
			case <-ctx.Done():
				_ = file.Close()
				return ctx.Err()
			default:
			}
			line, err := reader.ReadString('\n')
			if len(line) > 0 && err == nil {
				offset += int64(len(line))
				msg := line
				if len(msg) > 0 && msg[len(msg)-1] == '\n' {
					msg = msg[:len(msg)-1]
				}
				publish(model.Log{
					Level:   "INFO",
					Service: source.Name,
					Message: msg,
					Source:  "file",
				})
				continue
			}
			if err == io.EOF {
				stat, statErr := file.Stat()
				if statErr == nil {
					offset, _ = file.Seek(0, io.SeekCurrent)
					if fileInode(stat) != inode || stat.Size() < offset {
						_ = file.Close()
						break
					}
				}
				select {
				case <-ctx.Done():
					_ = file.Close()
					return ctx.Err()
				case <-time.After(250 * time.Millisecond):
				}
				continue
			}
			if err != nil {
				_ = file.Close()
				break
			}
		}
	}
}
